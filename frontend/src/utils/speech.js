

// Web Speech API 封装：浏览器不支持语音识别时返回 null，调用方据此隐藏麦克风。
export function speechSupported() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  return !!(SR && typeof SR === 'function')
}


export function createSpeech({ onText, onState } = {}) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return null

  const rec = new SR()
  rec.lang = 'zh-CN'
  rec.interimResults = true
  rec.continuous = false
  let finalText = ''

  rec.onresult = (e) => {
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i]
      if (r.isFinal) finalText += r[0].transcript
      else interim += r[0].transcript
    }
    if (onText) onText((finalText + interim).trim())
  }

  rec.onend = () => {
    if (onState) onState(false)
  }

  rec.onerror = () => {
    if (onState) onState(false)
  }

  return {
    start() {
      finalText = ''
      try {
        rec.start()
        if (onState) onState(true)
      } catch {
        
      }
    },
    stop() {
      try {
        rec.stop()
      } catch {
        
      }
    }
  }
}
