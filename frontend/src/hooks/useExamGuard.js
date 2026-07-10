import { useEffect } from 'react'

/**
 * Wires the browser-level exam-integrity listeners (clipboard, context menu,
 * inspect shortcuts, focus loss, fullscreen exit) for a live exam and reports
 * incidents through `logIncident`. Runs only while `liveExam` is set.
 */
export function useExamGuard(liveExam, logIncident) {
  useEffect(() => {
    if (!liveExam) return undefined

    const blockEvent = (event, incidentType, detail) => {
      event.preventDefault()
      logIncident(incidentType, detail)
    }

    const handleClipboard = (event) => {
      if (liveExam.block_clipboard) {
        blockEvent(event, event.type, `${event.type} was blocked during the live exam.`)
      }
    }

    const handleContextMenu = (event) => {
      if (liveExam.block_context_menu) {
        blockEvent(event, 'context_menu', 'Right-click was blocked during the live exam.')
      }
    }

    const handleKeyDown = (event) => {
      if (!liveExam.block_inspect_shortcuts) return
      const key = event.key.toLowerCase()
      const isInspectShortcut =
        event.key === 'F12' ||
        (event.ctrlKey && event.shiftKey && ['i', 'j', 'c'].includes(key)) ||
        (event.metaKey && event.altKey && ['i', 'j', 'c'].includes(key)) ||
        ((event.ctrlKey || event.metaKey) && key === 'u')
      if (isInspectShortcut) {
        blockEvent(event, 'inspect_shortcut', 'Developer-tool shortcut was blocked during the live exam.')
      }
    }

    const handleVisibilityChange = () => {
      if (liveExam.track_focus_loss && document.visibilityState === 'hidden') {
        logIncident('tab_switch', 'Tab switch or page hide detected during the live exam.')
      }
    }

    const handleBlur = () => {
      if (liveExam.track_focus_loss) {
        logIncident('window_blur', 'Exam window lost focus during the live exam.')
      }
    }

    const handleFullscreenChange = () => {
      if (liveExam.enforce_fullscreen && !document.fullscreenElement) {
        logIncident('fullscreen_exit', 'Fullscreen mode was exited during the live exam.')
      }
    }

    document.addEventListener('copy', handleClipboard)
    document.addEventListener('cut', handleClipboard)
    document.addEventListener('paste', handleClipboard)
    document.addEventListener('contextmenu', handleContextMenu)
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    window.addEventListener('blur', handleBlur)

    return () => {
      document.removeEventListener('copy', handleClipboard)
      document.removeEventListener('cut', handleClipboard)
      document.removeEventListener('paste', handleClipboard)
      document.removeEventListener('contextmenu', handleContextMenu)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
      window.removeEventListener('blur', handleBlur)
    }
  }, [liveExam, logIncident])
}
