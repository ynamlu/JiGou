// Markdown 渲染：代码高亮、代码块一键复制、外链新窗口安全打开。
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/common'

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

// 直接接管 fence 渲染：输出「标题栏 + 复制按钮 + 代码」的完整结构，
// 避免在 highlight() 里返回 <div> 后被 markdown-it 再包一层 <pre><code>。
md.renderer.rules.fence = (tokens, idx) => {
  const token = tokens[idx]
  const info = (token.info || '').trim()
  const lang = info.split(/\s+/g)[0] || ''
  const escaped = md.utils.escapeHtml(token.content)

  let highlighted = escaped
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(token.content, { language: lang, ignoreIllegals: true }).value
    } catch {
      highlighted = escaped
    }
  }

  const label = md.utils.escapeHtml(lang || 'text')
  return (
    `<div class="code-block"><div class="code-head">` +
    `<span class="code-lang">${label}</span>` +
    `<button type="button" class="copy-code-btn">复制</button>` +
    `</div><pre class="hljs"><code>${highlighted}</code></pre></div>\n`
  )
}

// 为外部链接统一添加 target="_blank" 与 rel="noopener noreferrer"，防止跳出 SPA 与安全风险
const defaultLinkRender =
  md.renderer.rules.link_open ||
  function (tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options)
  }

md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkRender(tokens, idx, options, env, self)
}

export function renderMarkdown(text) {
  return md.render(text || '')
}
