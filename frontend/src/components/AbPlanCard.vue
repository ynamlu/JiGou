<script setup>
defineProps({
  plan: { type: Object, default: null }
})
</script>

<template>
  <div v-if="plan" class="ab-plan-wrap">
    <div class="plans">
      <div v-if="plan.plan_a" class="plan plan-a">
        <div class="plan-badge">方案 A</div>
        <div class="plan-name">{{ plan.plan_a.name }}</div>
        <p class="plan-pos">{{ plan.plan_a.positioning }}</p>
        <div class="plan-meta">
          <span>预算：<b>{{ plan.plan_a.cost || '—' }}</b></span>
          <span>工期：<b>{{ plan.plan_a.duration || '—' }}</b></span>
        </div>
        <div class="plan-list-title">功能范围</div>
        <ul v-if="plan.plan_a.scope && plan.plan_a.scope.length" class="plan-list">
          <li v-for="(s, i) in plan.plan_a.scope" :key="i">{{ s }}</li>
        </ul>
        <div v-if="plan.plan_a.pros && plan.plan_a.pros.length" class="plan-list-title pro">优点</div>
        <ul v-if="plan.plan_a.pros" class="plan-list">
          <li v-for="(s, i) in plan.plan_a.pros" :key="i">{{ s }}</li>
        </ul>
        <div v-if="plan.plan_a.cons && plan.plan_a.cons.length" class="plan-list-title con">代价</div>
        <ul v-if="plan.plan_a.cons" class="plan-list">
          <li v-for="(s, i) in plan.plan_a.cons" :key="i">{{ s }}</li>
        </ul>
      </div>

      <div v-if="plan.plan_b" class="plan plan-b">
        <div class="plan-badge b">方案 B</div>
        <div class="plan-name">{{ plan.plan_b.name }}</div>
        <p class="plan-pos">{{ plan.plan_b.positioning }}</p>
        <div class="plan-meta">
          <span>预算：<b>{{ plan.plan_b.cost || '—' }}</b></span>
          <span>工期：<b>{{ plan.plan_b.duration || '—' }}</b></span>
        </div>
        <div class="plan-list-title">功能范围</div>
        <ul v-if="plan.plan_b.scope && plan.plan_b.scope.length" class="plan-list">
          <li v-for="(s, i) in plan.plan_b.scope" :key="i">{{ s }}</li>
        </ul>
        <div v-if="plan.plan_b.pros && plan.plan_b.pros.length" class="plan-list-title pro">优点</div>
        <ul v-if="plan.plan_b.pros" class="plan-list">
          <li v-for="(s, i) in plan.plan_b.pros" :key="i">{{ s }}</li>
        </ul>
        <div v-if="plan.plan_b.cons && plan.plan_b.cons.length" class="plan-list-title con">代价</div>
        <ul v-if="plan.plan_b.cons" class="plan-list">
          <li v-for="(s, i) in plan.plan_b.cons" :key="i">{{ s }}</li>
        </ul>
      </div>
    </div>
    <div v-if="plan.recommend" class="recommend-box">
      <span class="recommend-icon">💡</span>
      <p class="recommend-text"><b>建议：</b>{{ plan.recommend }}</p>
    </div>
  </div>
</template>

<style scoped>
.ab-plan-wrap {
  display: flex;
  flex-direction: column;
}

.plans {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.plan {
  position: relative;
  padding: 18px;
  border-radius: 16px;
  background: var(--card-2);
  border: 1.5px solid var(--line);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.plan:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.plan-a {
  border-color: rgba(79, 70, 229, 0.25);
}

.plan-b {
  border-color: rgba(14, 165, 164, 0.25);
}

.plan-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--accent-soft);
  color: var(--accent);
  margin-bottom: 8px;
}

.plan-badge.b {
  background: #e0f7f6;
  color: #0f766e;
}

.plan-name {
  font-size: 17px;
  font-weight: 750;
  color: #101a34;
}

.plan-pos {
  margin: 4px 0 12px;
  font-size: 13.5px;
  color: var(--ink-2);
  line-height: 1.6;
}

.plan-meta {
  display: flex;
  gap: 14px;
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--bg);
  border: 1px solid var(--line);
  font-size: 13px;
  color: var(--ink-2);
}

.plan-meta b {
  color: #101a34;
  font-weight: 700;
}

.plan-list-title {
  font-size: 13px;
  font-weight: 700;
  margin: 12px 0 6px;
  color: var(--ink);
}

.plan-list-title.pro {
  color: #059669;
}

.plan-list-title.con {
  color: #dc2626;
}

.plan-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.7;
  color: #334155;
}

.recommend-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fefce8;
  border: 1px solid #fef08a;
  color: #854d0e;
}

.recommend-icon {
  font-size: 18px;
  flex: none;
}

.recommend-text {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.65;
}

.recommend-text b {
  color: #713f12;
}
</style>
