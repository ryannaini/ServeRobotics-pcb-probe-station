import { useState, useEffect, useRef } from 'react'

const CAMERA_STREAM_URL = 'http://localhost:8000/stream'
const VOLTAGE_HISTORY_LEN = 80

function voltageRange(samples, channel) {
  if (!samples.length) {
    return channel === 1 ? { min: 0, max: 3.3 } : { min: 0, max: 5.0 }
  }
  let min = Math.min(...samples)
  let max = Math.max(...samples)
  const span = max - min || 0.5
  const pad = Math.max(span * 0.12, 0.08)
  min -= pad
  max += pad
  return { min, max }
}

function voltageTicks(min, max, count = 4) {
  const step = (max - min) / (count - 1)
  return Array.from({ length: count }, (_, i) => min + step * i)
}

function VoltageGraph({ samples, latestV, channel }) {
  const isRead = channel === 1
  const w = 520
  const h = 200
  const pad = { t: 14, r: 16, b: 28, l: 48 }
  const plotW = w - pad.l - pad.r
  const plotH = h - pad.t - pad.b
  const hasData = samples.length > 0
  const { min: yMin, max: yMax } = voltageRange(samples, channel)
  const gridYs = voltageTicks(yMin, yMax)

  const toY = (v) => {
    const t = (v - yMin) / (yMax - yMin || 1)
    return pad.t + plotH * (1 - Math.min(1, Math.max(0, t)))
  }

  const points = hasData
    ? samples
        .map((v, i) => {
          const x = pad.l + (i / Math.max(1, samples.length - 1)) * plotW
          return `${x},${toY(v)}`
        })
        .join(' ')
    : ''

  const formatV = (v) => {
    const abs = Math.abs(v)
    if (abs >= 100) return `${v.toFixed(0)}V`
    if (abs >= 10) return `${v.toFixed(1)}V`
    return `${v.toFixed(2)}V`
  }

  return (
    <div
      className={`voltage-graph-wrap ${isRead ? 'voltage-graph-read' : 'voltage-graph-inject'}`}
    >
      <svg
        className="voltage-graph-svg"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={isRead ? 'Voltage trace — Read channel' : 'Voltage trace — Inject channel'}
      >
        {gridYs.map((gv) => (
          <g key={gv}>
            <line
              x1={pad.l}
              y1={toY(gv)}
              x2={w - pad.r}
              y2={toY(gv)}
              className="voltage-grid-line"
            />
            <text x={6} y={toY(gv) + 4} className="voltage-axis-label">
              {formatV(gv)}
            </text>
          </g>
        ))}
        {!hasData && (
          <text
            x={w / 2}
            y={h / 2}
            className="voltage-empty-label"
            textAnchor="middle"
          >
            {isRead ? 'Read — awaiting data' : 'Inject — awaiting data'}
          </text>
        )}
        {points && (
          <>
            <polyline points={points} className="voltage-trace" fill="none" />
            <circle
              cx={pad.l + plotW}
              cy={toY(samples[samples.length - 1])}
              r={4}
              className="voltage-dot"
            />
          </>
        )}
      </svg>
      <div className="voltage-graph-meta">
        <code>{typeof latestV === 'number' ? `${latestV.toFixed(3)} V` : '—'}</code>
        <span className="voltage-graph-mode">
          {isRead ? 'Read · Ch 1' : 'Inject · Ch 2'}
        </span>
      </div>
    </div>
  )
}

const STEP_ICON = { pending: '○', running: '', done: '✓', failed: '✕' }

function LandingPage({ onInitialize, status, error, steps = [] }) {
  const isInitializing = status === 'initializing'
  const showSteps = isInitializing || steps.some((step) => step.state !== 'pending')

  return (
    <div className="landing">
      <div className="landing-bg" aria-hidden="true">
        <div className="landing-orb landing-orb-a" />
        <div className="landing-orb landing-orb-b" />
        <div className="landing-orb landing-orb-c" />
        <div className="landing-grid" />
        <div className="landing-vignette" />
      </div>

      <div className="landing-content">
        <p className="landing-brand">PCB Probe System</p>
        <h1 className="landing-headline">Before we begin programming</h1>
        <p className="landing-sub">Initialize the Robot</p>

        <button
          className="init-btn landing-init-btn"
          onClick={onInitialize}
          disabled={isInitializing}
        >
          {isInitializing ? 'Initializing...' : 'Initialize Robot'}
        </button>

        {showSteps && (
          <ul className="init-steps">
            {steps.map((step) => (
              <li key={step.id} className={`init-step init-step-${step.state}`}>
                <span className="init-step-icon">
                  {step.state === 'running' ? <span className="init-spinner" /> : STEP_ICON[step.state]}
                </span>
                <span className="init-step-label">{step.label}</span>
                {step.note && <span className="init-step-note">{step.note}</span>}
              </li>
            ))}
          </ul>
        )}

        {error && <p className="init-error">{error}</p>}
      </div>
    </div>
  )
}

// boardStatus carries the /initialize result for each Arduino, so a board that
// failed to connect shows up in its own panel instead of failing on first use.
function Dashboard({ boardStatus = {} }) {
  const [position, setPosition] = useState({
    x: 0, y: 0, z: 0, thetaX: 0, thetaY: 0, thetaZ: 0,
  })
  const [streamError, setStreamError] = useState('')
  const [cameraOk, setCameraOk] = useState(true)
  const [autofocusOn, setAutofocusOn] = useState(true)
  const [opticsError, setOpticsError] = useState('')
  const [channel, setChannel] = useState(1) // 1 = Read, 2 = Inject
  const [voltageSamples, setVoltageSamples] = useState([])
  const [latestVoltage, setLatestVoltage] = useState(null)
  const [injectVoltageInput, setInjectVoltageInput] = useState('')
  const [injectVoltage, setInjectVoltage] = useState(null) // applied 0–5 V
  const [injectError, setInjectError] = useState('')
  const [actuatorId, setActuatorId] = useState(null) // 3 = top, 4 = bottom
  const [actuatorSpeed, setActuatorSpeed] = useState(1) // 1 = slow, 2 = fast
  const [actuatorError, setActuatorError] = useState(
    boardStatus.actuator?.status === 'error' ? boardStatus.actuator.message : '',
  )
  const [flipError, setFlipError] = useState(
    boardStatus.flip?.status === 'error' ? boardStatus.flip.message : '',
  )
  const [flipNotice, setFlipNotice] = useState('')
  const actuatorHoldRef = useRef(false)
  const flipHoldRef = useRef(false)
  // Visual-only Z bias for In/Out bar (−1 = Out, 0 = center, +1 = In)
  const [zBias, setZBias] = useState(0)
  const [zScrollArmed, setZScrollArmed] = useState(false)
  const zSliderRef = useRef(null)

  useEffect(() => {
    if (!zScrollArmed) return
    const el = zSliderRef.current
    if (!el) return

    const onDocPointer = (e) => {
      if (!el.contains(e.target)) setZScrollArmed(false)
    }
    const onWheel = (e) => {
      e.preventDefault()
      e.stopPropagation()
      const step = e.deltaY > 0 ? -0.042 : 0.042
      setZBias((v) => Math.min(1, Math.max(-1, v + step)))
    }

    document.addEventListener('pointerdown', onDocPointer)
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => {
      document.removeEventListener('pointerdown', onDocPointer)
      el.removeEventListener('wheel', onWheel)
    }
  }, [zScrollArmed])

  const setProbeChannel = async (nextChannel) => {
    setChannel(nextChannel)
    setVoltageSamples([])
    setLatestVoltage(null)
    setInjectError('')
    if (nextChannel === 1) {
      setInjectVoltageInput('')
      setInjectVoltage(null)
    }
    // TODO: POST /channel?channel= when backend is ready
  }

  const applyInjectVoltage = () => {
    setInjectError('')
    const raw = injectVoltageInput.trim()
    if (raw === '') {
      setInjectError('Enter a voltage between 0 and 5 V')
      return
    }
    const v = Number(raw)
    if (Number.isNaN(v) || v < 0 || v > 5) {
      setInjectError('Voltage must be between 0 and 5 V')
      return
    }
    setInjectVoltage(v)
    // TODO: POST /inject?voltage= when backend is ready
  }

  // Selection and speed stay in the UI; the backend only opens the actuator
  // session on the first move, so the driver enable is not held low while
  // the operator is still choosing.
  const selectActuator = (id) => {
    setActuatorId(id)
    setActuatorError('')
    actuatorHoldRef.current = false
  }

  // The board answers OK / ERR busy / ERR <fault>. "busy" just means the
  // operator pressed something while it was already moving, so it reads as a
  // notice rather than a failure.
  const postFlip = async (url) => {
    setFlipNotice('')
    try {
      const response = await fetch(url, { method: 'POST' })
      const data = await response.json().catch(() => ({}))

      if (data.status === 'busy') {
        setFlipNotice(data.message)
        return false
      }
      if (!response.ok || data.status === 'error') {
        setFlipError(data.message || 'Flip command failed')
        return false
      }
      return true
    } catch {
      setFlipError('Could not reach flip board')
      return false
    }
  }

  const flipHome = async () => {
    setFlipError('')
    await postFlip('http://localhost:8000/flip/home')
  }

  const flip180 = async () => {
    setFlipError('')
    await postFlip('http://localhost:8000/flip/180')
  }

  const stopFlip = async () => {
    flipHoldRef.current = false
    await postFlip('http://localhost:8000/flip/stop')
  }

  const startFlipHold = async (dir) => {
    if (flipHoldRef.current) return
    flipHoldRef.current = true
    setFlipError('')
    const ccw = dir === 'ccw'
    const ok = await postFlip(`http://localhost:8000/flip/rotate?ccw=${ccw}`)
    if (!ok) flipHoldRef.current = false
  }

  const flipHoldProps = (dir) => ({
    onMouseDown: (e) => {
      e.preventDefault()
      startFlipHold(dir)
    },
    onMouseUp: stopFlip,
    onMouseLeave: stopFlip,
    onTouchStart: (e) => {
      e.preventDefault()
      startFlipHold(dir)
    },
    onTouchEnd: stopFlip,
    onTouchCancel: stopFlip,
  })

  const stopActuator = async () => {
    actuatorHoldRef.current = false
    try {
      await fetch('http://localhost:8000/actuator/stop', { method: 'POST' })
    } catch {
      setActuatorError('Could not reach actuator endpoint')
    }
  }

  const pulseActuator = async (dir) => {
    if (!actuatorId) return
    setActuatorError('')
    try {
      const response = await fetch(
        `http://localhost:8000/actuator/step?actuator=${actuatorId}&dir=${dir}&speed=${actuatorSpeed}`,
        { method: 'POST' },
      )
      const data = await response.json().catch(() => ({}))
      if (!response.ok || data.status === 'error') {
        setActuatorError(data.message || 'Actuator step failed')
      }
    } catch {
      setActuatorError('Could not reach actuator endpoint')
    }
  }

  const startActuatorHold = async (dir) => {
    if (!actuatorId || actuatorHoldRef.current) return
    actuatorHoldRef.current = true
    setActuatorError('')
    try {
      const response = await fetch(
        `http://localhost:8000/actuator/move?actuator=${actuatorId}&dir=${dir}&speed=${actuatorSpeed}`,
        { method: 'POST' },
      )
      const data = await response.json().catch(() => ({}))
      if (!response.ok || data.status === 'error') {
        setActuatorError(data.message || 'Actuator move failed')
        actuatorHoldRef.current = false
      }
    } catch {
      setActuatorError('Could not reach actuator endpoint')
      actuatorHoldRef.current = false
    }
  }

  const actuatorHoldProps = (dir) => ({
    disabled: !actuatorId,
    onMouseDown: (e) => {
      e.preventDefault()
      startActuatorHold(dir)
    },
    onMouseUp: stopActuator,
    onMouseLeave: stopActuator,
    onTouchStart: (e) => {
      e.preventDefault()
      startActuatorHold(dir)
    },
    onTouchEnd: stopActuator,
    onTouchCancel: stopActuator,
  })

  const actuatorStartRef = useRef(startActuatorHold)
  const actuatorStopRef = useRef(stopActuator)
  actuatorStartRef.current = startActuatorHold
  actuatorStopRef.current = stopActuator

  // Remount feed when dashboard opens so a prior 404 doesn't stick forever
  useEffect(() => {
    setCameraOk(true)
  }, [])

  const holdingRef = useRef(false)
  const jogRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/position')

    ws.onopen = () => setStreamError('')
    ws.onerror = () => setStreamError('WebSocket error — is the backend running on :8000?')
    ws.onclose = () => setStreamError('Position stream disconnected')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.status === 'ok') {
        setStreamError('')
        setPosition(data.message)
      } else {
        setStreamError(data.message || 'Position stream error')
      }
    }

    return () => ws.close()
  }, [])

  const homeArm = async () => {
    await fetch('http://localhost:8000/home', { method: 'POST' })
  }

  const jog = async (dx, dy) => {
    await fetch(`http://localhost:8000/jog?dx=${dx}&dy=${dy}`, { method: 'POST' })
  }
  jogRef.current = jog

  const setAutofocus = async (enable) => {
    setOpticsError('')
    try {
      const response = await fetch(
        `http://localhost:8000/autofocus?enable=${enable}`,
        { method: 'POST' },
      )
      const data = await response.json().catch(() => ({}))
      if (!response.ok || data.status === 'error') {
        setOpticsError(data.message || 'Autofocus request failed')
        return
      }
      setAutofocusOn(enable)
    } catch {
      setOpticsError('Could not reach autofocus endpoint')
    }
  }

  const focusStep = async (delta) => {
    setOpticsError('')
    try {
      const response = await fetch(
        `http://localhost:8000/focus?delta=${delta}`,
        { method: 'POST' },
      )
      const data = await response.json().catch(() => ({}))
      if (!response.ok || data.status === 'error') {
        setOpticsError(data.message || 'Focus step failed')
      }
    } catch {
      setOpticsError('Could not reach focus endpoint')
    }
  }

  const startHoldJog = async (dx, dy) => {
    if (holdingRef.current) return
    holdingRef.current = true
    while (holdingRef.current) {
      await jogRef.current(dx, dy)
    }
  }

  const stopHoldJog = () => {
    holdingRef.current = false
  }

  // WASD: W up, A left, S down, D right (same deltas as the D-pad)
  useEffect(() => {
    const keyMap = {
      w: [0, 1],
      a: [-1, 0],
      s: [0, -1],
      d: [1, 0],
    }

    const onKeyDown = (e) => {
      const k = e.key.toLowerCase()
      if (k === 's' && actuatorHoldRef.current) return
      const delta = keyMap[k]
      if (!delta || e.repeat) return
      e.preventDefault()
      startHoldJog(delta[0], delta[1])
    }

    const onKeyUp = (e) => {
      if (keyMap[e.key.toLowerCase()]) stopHoldJog()
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      stopHoldJog()
    }
  }, [])

  // F / B hold-to-move when an actuator is selected (matches Arduino serial)
  useEffect(() => {
    if (!actuatorId) return undefined

    const onKeyDown = (e) => {
      if (e.repeat) return
      const k = e.key.toLowerCase()
      if (k === 'f') {
        e.preventDefault()
        actuatorStartRef.current('forward')
      } else if (k === 'b') {
        e.preventDefault()
        actuatorStartRef.current('backward')
      } else if (k === 's' && actuatorHoldRef.current) {
        e.preventDefault()
        actuatorStopRef.current()
      }
    }

    const onKeyUp = (e) => {
      const k = e.key.toLowerCase()
      if (k === 'f' || k === 'b') actuatorStopRef.current()
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      actuatorStopRef.current()
    }
  }, [actuatorId])

  const holdProps = (dx, dy) => ({
    onMouseDown: (e) => {
      e.preventDefault()
      startHoldJog(dx, dy)
    },
    onMouseUp: stopHoldJog,
    onMouseLeave: stopHoldJog,
    onTouchStart: (e) => {
      e.preventDefault()
      startHoldJog(dx, dy)
    },
    onTouchEnd: stopHoldJog,
    onTouchCancel: stopHoldJog,
  })

  const fmt = (n) => (typeof n === 'number' ? n.toFixed(4) : n)

  return (
    <div className="dashboard">
      <header className="dash-header">
        <span className="dash-brand">PCB Probe System</span>
        <span className="dash-hint">WASD or D-pad to jog</span>
      </header>

      <div className="dash-layout">
        <div className="dash-left">
          <section className="camera-panel">
            <div className="camera-frame">
              {cameraOk ? (
                <img
                  className="camera-feed"
                  src={CAMERA_STREAM_URL}
                  alt="Live camera feed"
                  onError={() => setCameraOk(false)}
                />
              ) : (
                <div className="camera-placeholder">
                  <span>Live camera</span>
                  <span className="camera-placeholder-sub">
                    Waiting for {CAMERA_STREAM_URL}
                  </span>
                </div>
              )}
            </div>
          </section>

          <section className="voltage-panel">
            <div className="voltage-panel-head">
              <h2>Voltage</h2>
              <span className="voltage-panel-hint">Live · LabJack</span>
            </div>
            <VoltageGraph
              samples={voltageSamples}
              latestV={latestVoltage}
              channel={channel}
            />
          </section>

          <section className="channel-panel control-card">
            <div className="panel-head">
              <span className="panel-label">Switch channel</span>
              <span className={`panel-badge ${channel === 1 ? 'panel-badge-read' : 'panel-badge-inject'}`}>
                {channel === 1 ? 'Ch 1 · Read' : 'Ch 2 · Inject'}
              </span>
            </div>

            <div className="channel-body">
              <div className="channel-segment" role="group" aria-label="Probe channel">
                <button
                  type="button"
                  className={`channel-seg-btn ${channel === 1 ? 'channel-seg-btn-active' : ''}`}
                  aria-pressed={channel === 1}
                  onClick={() => setProbeChannel(1)}
                >
                  <span className="channel-num">1</span>
                  Read
                </button>
                <button
                  type="button"
                  className={`channel-seg-btn ${channel === 2 ? 'channel-seg-btn-active' : ''}`}
                  aria-pressed={channel === 2}
                  onClick={() => setProbeChannel(2)}
                >
                  <span className="channel-num">2</span>
                  Inject
                </button>
              </div>

              <div className={`channel-detail ${channel === 2 ? 'channel-detail-inject' : 'channel-detail-read'}`}>
                {channel === 1 ? (
                  <>
                    <p className="channel-detail-title">Multimeter path</p>
                    <p className="channel-detail-desc">
                      Relay routes the probe to the read channel. Voltage trace above shows live LabJack data.
                    </p>
                  </>
                ) : (
                  <>
                    <label className="inject-label" htmlFor="inject-voltage">
                      Inject voltage (0–5 V)
                    </label>
                    <div className="inject-row">
                      <input
                        id="inject-voltage"
                        className="inject-input"
                        type="number"
                        min={0}
                        max={5}
                        step={0.01}
                        placeholder="e.g. 3.3"
                        value={injectVoltageInput}
                        onChange={(e) => {
                          setInjectVoltageInput(e.target.value)
                          setInjectError('')
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') applyInjectVoltage()
                        }}
                      />
                      <button
                        type="button"
                        className="inject-apply-btn"
                        onClick={applyInjectVoltage}
                      >
                        Set
                      </button>
                    </div>
                    {injectVoltage !== null && (
                      <p className="inject-applied">
                        Target: <code>{injectVoltage.toFixed(2)} V</code>
                      </p>
                    )}
                    {injectError && <p className="init-error inject-error">{injectError}</p>}
                  </>
                )}
              </div>
            </div>
          </section>
        </div>

        <aside className="controls-panel">
          <h2>Live Position</h2>
          {streamError && <p className="init-error">{streamError}</p>}

          <div className="controls-stack">
          <div className="telemetry">
            <div className="telemetry-row"><span>X</span><code>{fmt(position.x)} m</code></div>
            <div className="telemetry-row"><span>θX</span><code>{fmt(position.thetaX)}°</code></div>
            <div className="telemetry-row"><span>Y</span><code>{fmt(position.y)} m</code></div>
            <div className="telemetry-row"><span>θY</span><code>{fmt(position.thetaY)}°</code></div>
            <div className="telemetry-row"><span>Z</span><code>{fmt(position.z)} m</code></div>
            <div className="telemetry-row"><span>θZ</span><code>{fmt(position.thetaZ)}°</code></div>
          </div>

          <div className="controls-jog">
          <div className="jog-cluster">
            <div className="dpad">
              <button className="dpad-btn" type="button" {...holdProps(0, 1)}>↑</button>
              <div className="dpad-row">
                <button className="dpad-btn" type="button" {...holdProps(-1, 0)}>←</button>
                <button className="dpad-btn dpad-home" type="button" onClick={homeArm}>Home</button>
                <button className="dpad-btn" type="button" {...holdProps(1, 0)}>→</button>
              </div>
              <button className="dpad-btn" type="button" {...holdProps(0, -1)}>↓</button>
            </div>

            <div
              ref={zSliderRef}
              className={`z-slider ${zScrollArmed ? 'z-slider-armed' : ''}`}
              aria-label="Robot in and out"
              tabIndex={0}
              onClick={() => {
                setZScrollArmed(true)
                zSliderRef.current?.focus()
              }}
            >
              <span className="z-slider-end">In</span>
              <div
                className="z-slider-track"
                onPointerDown={(e) => {
                  e.stopPropagation()
                  setZScrollArmed(true)
                  zSliderRef.current?.focus()
                  const track = e.currentTarget
                  const move = (clientY) => {
                    const rect = track.getBoundingClientRect()
                    const t = Math.min(1, Math.max(0, (clientY - rect.top) / rect.height))
                    // Top = In (+1), bottom = Out (−1)
                    setZBias(1 - 2 * t)
                  }
                  move(e.clientY)
                  track.setPointerCapture(e.pointerId)
                  const onMove = (ev) => move(ev.clientY)
                  const onUp = () => {
                    track.releasePointerCapture(e.pointerId)
                    track.removeEventListener('pointermove', onMove)
                    track.removeEventListener('pointerup', onUp)
                  }
                  track.addEventListener('pointermove', onMove)
                  track.addEventListener('pointerup', onUp)
                }}
              >
                <div className="z-slider-mid" />
                <div
                  className="z-slider-node"
                  style={{ top: `${((1 - zBias) / 2) * 100}%` }}
                  role="slider"
                  aria-valuemin={-1}
                  aria-valuemax={1}
                  aria-valuenow={zBias}
                  aria-valuetext={zBias > 0.05 ? 'In' : zBias < -0.05 ? 'Out' : 'Center'}
                />
              </div>
              <span className="z-slider-end">Out</span>
            </div>
          </div>

          <p className="wasd-legend">W ↑ &nbsp; A ← &nbsp; S ↓ &nbsp; D →</p>
          </div>

          <div className="optics-bar control-card">
            <div className="optics-row">
              <span className="panel-label">Autofocus</span>
              <button
                type="button"
                className={`af-switch ${autofocusOn ? 'af-switch-on' : ''}`}
                aria-pressed={autofocusOn}
                onClick={() => setAutofocus(!autofocusOn)}
              >
                <span className="af-switch-knob" />
                <span className="af-switch-text">{autofocusOn ? 'ON' : 'OFF'}</span>
              </button>
            </div>

            <div className={`focus-step ${autofocusOn ? 'focus-step-dim' : 'focus-step-active'}`}>
              <span className="panel-label">Focus step</span>
              <div className="focus-step-btns">
                <button
                  type="button"
                  className="focus-step-btn"
                  disabled={autofocusOn}
                  onClick={() => focusStep(-10)}
                  aria-label="Focus minus"
                >
                  −
                </button>
                <button
                  type="button"
                  className="focus-step-btn"
                  disabled={autofocusOn}
                  onClick={() => focusStep(10)}
                  aria-label="Focus plus"
                >
                  +
                </button>
              </div>
            </div>

            {opticsError && <p className="init-error optics-error">{opticsError}</p>}
          </div>

          <div className="actuator-bar control-card">
            <span className="panel-label">Linear actuator (Probe)</span>

            <div className="actuator-step">
              <span className="actuator-step-label">1 · Select</span>
              <div className="actuator-toggle" role="group" aria-label="Actuator selection">
                <button
                  type="button"
                  className={`actuator-btn ${actuatorId === 3 ? 'actuator-btn-active' : ''}`}
                  aria-pressed={actuatorId === 3}
                  onClick={() => selectActuator(3)}
                >
                  Top
                </button>
                <button
                  type="button"
                  className={`actuator-btn ${actuatorId === 4 ? 'actuator-btn-active' : ''}`}
                  aria-pressed={actuatorId === 4}
                  onClick={() => selectActuator(4)}
                >
                  Bottom
                </button>
              </div>
            </div>

            {actuatorId && (
              <>
                <div className="actuator-step">
                  <span className="actuator-step-label">2 · Speed</span>
                  <div className="actuator-speed" role="group" aria-label="Actuator speed">
                    <button
                      type="button"
                      className={`actuator-speed-btn ${actuatorSpeed === 1 ? 'actuator-speed-btn-active' : ''}`}
                      aria-pressed={actuatorSpeed === 1}
                      onClick={() => setActuatorSpeed(1)}
                    >
                      Slow
                    </button>
                    <button
                      type="button"
                      className={`actuator-speed-btn ${actuatorSpeed === 2 ? 'actuator-speed-btn-active' : ''}`}
                      aria-pressed={actuatorSpeed === 2}
                      onClick={() => setActuatorSpeed(2)}
                    >
                      Fast
                    </button>
                  </div>
                </div>

                <div className="actuator-step">
                  <span className="actuator-step-label">3 · Move</span>
                  <div className="actuator-move-row">
                    <button
                      type="button"
                      className="actuator-move-btn"
                      {...actuatorHoldProps('backward')}
                    >
                      ← Back (b)
                    </button>
                    <button
                      type="button"
                      className="actuator-stop-btn"
                      onClick={stopActuator}
                    >
                      Stop (s)
                    </button>
                    <button
                      type="button"
                      className="actuator-move-btn"
                      {...actuatorHoldProps('forward')}
                    >
                      Fwd (f) →
                    </button>
                  </div>
                  <button
                    type="button"
                    className="actuator-step-once-btn"
                    onClick={() => pulseActuator('forward')}
                  >
                    Single step forward
                  </button>
                </div>
              </>
            )}

            {actuatorError && <p className="init-error actuator-error">{actuatorError}</p>}
          </div>

          <div className="flip-bar control-card">
            <span className="panel-label">Flip motorboard</span>

            <button type="button" className="flip-home-btn" onClick={flipHome}>
              Home position
            </button>

            <div className="flip-move-row">
              <button type="button" className="flip-move-btn" {...flipHoldProps('ccw')}>
                ↺ CCW
              </button>
              <button type="button" className="flip-stop-btn" onClick={stopFlip}>
                Stop
              </button>
              <button type="button" className="flip-move-btn" {...flipHoldProps('cw')}>
                CW ↻
              </button>
            </div>

            <button type="button" className="flip-180-btn" onClick={flip180}>
              Flip 180°
            </button>

            {flipNotice && <p className="flip-notice">{flipNotice}</p>}
            {flipError && <p className="init-error flip-error">{flipError}</p>}
          </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

const INITIAL_STEPS = [
  { id: 'arm', label: 'Robot arm — connect and move home', state: 'pending', note: '' },
  { id: 'boards', label: 'Arduino boards — actuator and flip', state: 'pending', note: '' },
]

function App() {
  const [stage, setStage] = useState('landing')
  const [error, setError] = useState('')
  const [boardStatus, setBoardStatus] = useState({})
  const [steps, setSteps] = useState(INITIAL_STEPS)

  useEffect(() => {
    if (import.meta.env.DEV && window.location.search.includes('demo')) {
      setStage('ready')
    }
  }, [])

  const markStep = (id, patch) =>
    setSteps((prev) => prev.map((step) => (step.id === id ? { ...step, ...patch } : step)))

  const runStep = async (id, url, timeoutMs) => {
    markStep(id, { state: 'running', note: '' })
    try {
      const response = await fetch(url, { method: 'POST', signal: AbortSignal.timeout(timeoutMs) })
      const data = await response.json().catch(() => ({}))
      const ok = response.ok && data.status === 'ok'
      // FastAPI's own errors (404, 422) carry only `detail`, so fall back to
      // the HTTP status rather than printing "undefined".
      const message = data.message || (response.ok ? '' : `HTTP ${response.status}`)
      markStep(id, {
        state: ok ? 'done' : 'failed',
        note: ok ? message : [message, data.detail].filter(Boolean).join(' — ') || 'Failed',
      })
      return { ok, data }
    } catch (err) {
      markStep(id, {
        state: 'failed',
        note: err.name === 'TimeoutError' ? 'Timed out' : 'Could not reach the backend',
      })
      return { ok: false, data: {} }
    }
  }

  const initializeArm = async () => {
    setStage('initializing')
    setError('')
    setSteps(INITIAL_STEPS)

    // Homing takes ~15s and the backend gives up on the arm at 60s, so allow a
    // little more than that before calling it a lost cause.
    const arm = await runStep('arm', 'http://localhost:8000/initialize/arm', 90_000)
    if (!arm.ok) {
      setError('Robot did not reach READY — the dashboard needs the arm.')
      setStage('landing')
      return
    }

    // Each board opens its port with a 2s reset wait, so this step is short.
    const boards = await runStep('boards', 'http://localhost:8000/initialize/boards', 30_000)
    setBoardStatus({ actuator: boards.data.actuator, flip: boards.data.flip })

    // A board that failed is reported in its own panel rather than blocking
    // entry, but hold briefly so the ticks are readable before we switch.
    await new Promise((resolve) => setTimeout(resolve, 700))
    setStage('ready')
  }

  if (stage === 'ready') {
    return <Dashboard boardStatus={boardStatus} />
  }

  return <LandingPage onInitialize={initializeArm} status={stage} error={error} steps={steps} />
}

export default App
