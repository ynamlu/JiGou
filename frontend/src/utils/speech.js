// Web Speech API 封装。
// 语音识别对运行环境要求较高：浏览器需支持、页面需处于安全上下文（HTTPS/localhost）、
// 麦克风需授权；Chrome 还需要能访问其语音服务。这里把这些情况都转成可读提示。

function getRecognition() {
  if (typeof window === 'undefined') return null
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  return typeof SR === 'function' ? SR : null
}

export function speechSupport() {
  if (!getRecognition()) return { ok: false, reason: 'unsupported' }
  if (!window.isSecureContext) return { ok: false, reason: 'insecure' }
  return { ok: true, reason: '' }
}

export function speechSupported() {
  return speechSupport().ok
}

export function speechHint(reason) {
  if (reason === 'insecure') {
    return '语音输入需要 HTTPS 或 localhost。手机通过局域网 IP（http://192.168.x.x）访问时浏览器会禁用麦克风，请改用文字输入。'
  }
  if (reason === 'unsupported') {
    return '当前浏览器不支持语音识别，建议使用最新版 Chrome 或 Edge。'
  }
  return '语音输入暂不可用，请改用文字输入。'
}

export async function ensureMicrophone() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    return { ok: false, message: '当前浏览器不支持麦克风采集，请改用文字输入。' }
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    stream.getTracks().forEach((track) => track.stop())
    return { ok: true }
  } catch (err) {
    const name = (err && err.name) || ''
    if (name === 'NotAllowedError' || name === 'SecurityError') {
      return {
        ok: false,
        message: '麦克风权限被拒绝：请点击地址栏左侧的图标，允许麦克风后重试。'
      }
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
      return { ok: false, message: '没有检测到麦克风设备，请检查系统声音设置。' }
    }
    if (name === 'NotReadableError') {
      return { ok: false, message: '麦克风被其它程序占用，请关闭占用程序后重试。' }
    }
    return { ok: false, message: '无法访问麦克风：' + (err.message || name || '未知错误') }
  }
}

function errorMessage(code) {
  switch (code) {
    case 'not-allowed':
    case 'service-not-allowed':
      return '麦克风或语音服务被拒绝：请在浏览器设置中允许麦克风后重试。'
    case 'audio-capture':
      return '没有可用的麦克风，请检查设备后重试。'
    case 'network':
      return '语音服务连接失败：Chrome 需要访问其语音服务，国内网络常被拦截。建议改用 Edge 打开，或直接使用文字输入。'
    case 'no-speech':
      return '没有听到声音，请靠近麦克风、放慢语速后重试。'
    case 'language-not-supported':
      return '当前浏览器不支持中文语音识别，请改用文字输入。'
    case 'aborted':
      return ''
    default:
      return `语音识别失败（${code || '未知错误'}），请改用文字输入。`
  }
}

export function createSpeech({ onText, onState, onError } = {}) {
  const Ctor = getRecognition()
  if (!Ctor) return null

  const rec = new Ctor()
  rec.lang = 'zh-CN'
  rec.interimResults = true
  rec.continuous = false
  rec.maxAlternatives = 1
  let finalText = ''

  rec.onresult = (e) => {
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i += 1) {
      const r = e.results[i]
      if (r.isFinal) finalText += r[0].transcript
      else interim += r[0].transcript
    }
    if (onText) onText((finalText + interim).trim())
  }

  rec.onerror = (e) => {
    if (onState) onState(false)
    const msg = errorMessage(e && e.error)
    if (msg && onError) onError(msg)
  }

  rec.onend = () => {
    if (onState) onState(false)
  }

  return {
    start() {
      finalText = ''
      try {
        rec.start()
        if (onState) onState(true)
      } catch (err) {
        if (onState) onState(false)
        if (onError) onError('语音识别启动失败：' + (err.message || '请重试'))
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
