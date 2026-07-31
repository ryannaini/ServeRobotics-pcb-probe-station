import { useState, useEffect, useRef } from 'react'

const CAMERA_STREAM_URL = 'http://localhost:8000/stream'

function LandingPage({ onInitialize, status, error }) {
  const isInitializing = status === 'initializing'

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

        {error && <p className="init-error">{error}</p>}
      </div>
    </div>
  )
}

function Dashboard() {
  const [position, setPosition] = useState({
    x: 0, y: 0, z: 0, thetaX: 0, thetaY: 0, thetaZ: 0,
  })
  const [streamError, setStreamError] = useState('')
  const [cameraOk, setCameraOk] = useState(true)
  const [autofocusOn, setAutofocusOn] = useState(true)
  const [opticsError, setOpticsError] = useState('')
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
      const delta = keyMap[e.key.toLowerCase()]
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

        <aside className="controls-panel">
          <h2>Live Position</h2>
          {streamError && <p className="init-error">{streamError}</p>}

          <div className="telemetry">
            <div className="telemetry-row"><span>X</span><code>{fmt(position.x)} m</code></div>
            <div className="telemetry-row"><span>θX</span><code>{fmt(position.thetaX)}°</code></div>
            <div className="telemetry-row"><span>Y</span><code>{fmt(position.y)} m</code></div>
            <div className="telemetry-row"><span>θY</span><code>{fmt(position.thetaY)}°</code></div>
            <div className="telemetry-row"><span>Z</span><code>{fmt(position.z)} m</code></div>
            <div className="telemetry-row"><span>θZ</span><code>{fmt(position.thetaZ)}°</code></div>
          </div>

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

          <div className="optics-bar">
            <div className="optics-row">
              <span className="optics-label">Autofocus</span>
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
              <span className="optics-label">Focus step</span>
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
        </aside>
      </div>
    </div>
  )
}

function App() {
  const [stage, setStage] = useState('landing')
  const [error, setError] = useState('')

  const initializeArm = async () => {
    setStage('initializing')
    setError('')

    try {
      const response = await fetch('http://localhost:8000/initialize', { method: 'POST' })
      const data = await response.json()

      if (data.status === 'ok') {
        setStage('ready')
      } else {
        setError(data.message || 'Initialization failed')
        setStage('landing')
      }
    } catch (err) {
      setError('Could not reach the backend. Is it running?')
      setStage('landing')
    }
  }

  if (stage === 'ready') {
    return <Dashboard />
  }

  return <LandingPage onInitialize={initializeArm} status={stage} error={error} />
}

export default App
