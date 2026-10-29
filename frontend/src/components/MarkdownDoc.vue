<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps({
  source: {
    type: String,
    default: ''
  }
})

// 报告固定以「# 标题 + ## 章节」组织，这里按 ## 拆成可独立阅读的章节块。
const sections = computed(() => {
  const src = (props.source || '').trim()
  if (!src) return []

  const chunks = src.split(/^##\s+/m)
  const result = []

  const first = chunks[0].trim()
  const titleMatch = first.match(/^#\s+(.+)$/m)
  const introTitle = titleMatch ? titleMatch[1].trim() : ''
  const introBody = first.replace(/^#\s+.+$/m, '').trim()
  if (introTitle || introBody) {
    result.push({ title: introTitle, html: renderMarkdown(introBody), intro: true })
  }

  for (let i = 1; i < chunks.length; i += 1) {
    const lines = chunks[i].split('\n')
    const title = lines.shift().trim()
    const body = lines.join('\n').trim()
    result.push({ title, html: renderMarkdown(body), intro: false })
  }

  return result
})
</script>

<template>
  <div class="markdown-doc">
    <section
      v-for="(section, index) in sections"
      :key="index"
      class="doc-section"
      :class="{ intro: section.intro }"
    >
      <h1 v-if="section.intro && section.title" class="doc-title">{{ section.title }}</h1>
      <h2 v-else-if="section.title" class="section-title">
        <span class="section-bar"></span>
        {{ section.title }}
      </h2>
      <div class="section-body" v-html="section.html"></div>
    </section>
  </div>
</template>

<style scoped>
.markdown-doc {
  display: flex;
  flex-direction: column;
}

.doc-section {
  position: relative;
  padding: 0 0 24px;
  margin: 0 0 24px;
  border-bottom: 1px dashed var(--line-strong);
}

.doc-section:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: none;
}

.doc-section.intro {
  padding-bottom: 26px;
  margin-bottom: 26px;
  border-bottom: 1px solid var(--line);
}

.doc-section.intro::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 76px;
  height: 3px;
  border-radius: 2px;
  background: var(--grad);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 12px;
  font-size: 19px;
  font-weight: 750;
  letter-spacing: -0.2px;
}

.doc-title {
  margin: 0 0 14px;
  font-size: 27px;
  font-weight: 800;
  letter-spacing: -0.6px;
  color: #101a34;
  line-height: 1.35;
}

.section-bar {
  width: 4px;
  height: 19px;
  border-radius: 2px;
  background: var(--grad);
}

.section-body :deep(h1) {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #101a34;
}

.section-body :deep(h2) {
  font-size: 17px;
  margin: 14px 0 6px;
}

.section-body :deep(h3) {
  font-size: 15px;
  margin: 12px 0 4px;
}

.section-body :deep(p) {
  margin: 8px 0;
  font-size: 14.5px;
  line-height: 1.9;
  color: #334155;
}

.section-body :deep(ul),
.section-body :deep(ol) {
  margin: 8px 0;
  padding-left: 22px;
}

.section-body :deep(li) {
  font-size: 14.5px;
  line-height: 1.8;
  margin: 5px 0;
  color: #334155;
}

.section-body :deep(strong) {
  color: var(--accent);
}

.section-body :deep(blockquote) {
  border-left: 3px solid var(--accent-soft);
  padding-left: 10px;
  color: var(--ink-2);
  font-size: 13px;
  margin: 6px 0;
}

.section-body :deep(code) {
  background: var(--accent-soft);
  color: var(--accent);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
}

@media (max-width: 640px) {
  .doc-section {
    padding-bottom: 18px;
    margin-bottom: 18px;
  }

  .doc-section.intro {
    padding-bottom: 20px;
    margin-bottom: 20px;
  }

  .section-title {
    font-size: 17px;
    margin-bottom: 10px;
  }

  .section-body :deep(h1) {
    font-size: 21px;
  }

  .section-body :deep(p),
  .section-body :deep(li) {
    font-size: 14px;
    line-height: 1.85;
  }
}
</style>
