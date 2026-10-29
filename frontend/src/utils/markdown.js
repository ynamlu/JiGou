// Markdown 渲染统一关闭原始 HTML，避免模型输出里的标签被执行（XSS）。
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

export function renderMarkdown(text) {
  return md.render(text || '')
}
