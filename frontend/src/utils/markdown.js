// Markdown 渲染：语法高亮、代码块一键复制、外链新窗口安全打开。
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/common'

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  highlight(str, lang) {
    let highlighted = ''
    if (lang && hljs.getLanguage(lang)) {
      try {
        highlighted = hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
      } catch {
        highlighted = md.utils.escapeHtml(str)
      }
    } else {
      highlighted = md.utils.escapeHtml(str)
    }

    const langLabel = lang || 'code'
    return `<div class="code-block"><div class="code-head"><span class="code-lang">${md.utils.escapeHtml(
      langLabel
    )}</span><button type="button" class="copy-code-btn">复制</button></div><pre class="hljs"><code>${highlighted}</code></pre></div>`
  }
})

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
