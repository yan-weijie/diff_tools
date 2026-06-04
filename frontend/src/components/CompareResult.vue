<template>
  <section class="card cr-card">
    <!-- 头部：标题 + 过滤 + 搜索 + 导出 -->
    <div class="cr-head">
      <div class="cr-title">
        <span class="cr-label">对比结果</span>
        <span v-if="result" class="hint">
          {{ result.totalNew }} vs {{ result.totalOld }} · 差异 {{ result.diffCount }} / {{ result.commonCount }}
        </span>
        <span v-else class="hint">点击 "开始对比" 后展示</span>
      </div>
      <div class="cr-actions">
        <div class="tabs">
          <button v-for="f in filters" :key="f.value" class="tab"
                  :class="{ active: filter === f.value }" @click="filter = f.value">
            {{ f.label }}
          </button>
        </div>
        <input v-model="keyword" placeholder="搜索主键..." class="input mono" style="width:180px;height:32px;" />
        <button class="btn" :disabled="!result" @click="onExport">⤓ 导出 CSV</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="cr-error">⚠ {{ error }}</div>

    <!-- 统计卡片 -->
    <div v-if="result" class="cr-stats">
      <div class="stat"><div class="lbl">新数据总数</div><div class="val">{{ result.totalNew }}</div></div>
      <div class="stat"><div class="lbl">旧数据总数</div><div class="val">{{ result.totalOld }}</div></div>
      <div class="stat"><div class="lbl">共有记录</div><div class="val blue">{{ result.commonCount }}</div></div>
      <div class="stat"><div class="lbl">差异记录</div><div class="val red">{{ result.diffCount }}</div></div>
      <div class="stat"><div class="lbl">仅新存在</div><div class="val amber">{{ result.onlyInNew.length }}</div></div>
      <div class="stat"><div class="lbl">仅旧存在</div><div class="val amber">{{ result.onlyInOld.length }}</div></div>
    </div>

    <!-- 列表 -->
    <div class="cr-body">
      <div v-if="!result && !error" class="empty">
        <div class="empty-icon">📦</div>
        <p>暂无对比结果，请先在上方面板输入数据后点击 <b>"开始对比"</b></p>
      </div>
      <div v-else-if="result && items.length === 0" class="empty">
        <div class="empty-icon">🔍</div>
        <p>没有符合条件的结果</p>
      </div>

      <template v-for="(it, idx) in items" :key="idx">
        <!-- 共有记录对比卡 -->
        <details v-if="it.kind === 'compare'" class="cmp-card">
          <summary class="cmp-summary">
            <div class="cmp-summary-left">
              <span class="chev" style="color:#94a3b8;">▶</span>
              <span class="mono cmp-key">{{ it.data.key }}</span>
              <span v-if="it.data.hasDiff" class="chip chip-red">⚠ {{ diffNum(it.data) }} 处差异</span>
              <span v-else class="chip chip-green">✓ 完全一致</span>
            </div>
            <span class="hint">共 {{ it.data.fields.length }} 个字段</span>
          </summary>

          <!-- 组内过滤工具栏 -->
          <div class="cmp-toolbar">
            <div class="tabs">
              <button
                v-for="opt in groupFilters"
                :key="opt.value"
                class="tab"
                :class="{ active: getGroupFilter(it.data.key) === opt.value }"
                @click.stop="setGroupFilter(it.data.key, opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
            <span class="hint">
              显示 {{ filterFields(it.data, getGroupFilter(it.data.key)).length }} / {{ it.data.fields.length }}
            </span>
          </div>

          <div class="cmp-table-wrap scroll-thin">
            <table class="compare-table">
              <thead>
                <tr>
                  <th>新字段</th><th>新值</th><th>类型</th>
                  <th>旧字段</th><th>旧值</th><th>类型</th>
                  <th style="text-align:center;">结果</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(f, i) in filterFields(it.data, getGroupFilter(it.data.key))"
                  :key="i"
                  :class="f.same ? 'same' : 'diff'"
                >
                  <td class="mono">{{ f.newField }}</td>
                  <td class="mono" :class="f.same ? 'cell-same' : 'cell-diff'" v-html="formatVal(f.newVal)" />
                  <td><span class="hint">{{ f.newType }}</span></td>
                  <td class="mono">{{ f.oldField }}</td>
                  <td class="mono" :class="f.same ? 'cell-same' : 'cell-diff'" v-html="formatVal(f.oldVal)" />
                  <td><span class="hint">{{ f.oldType }}</span></td>
                  <td style="text-align:center;">
                    <span v-if="f.same" style="color:#16a34a;">✓</span>
                    <span v-else style="color:#dc2626;">✕</span>
                  </td>
                </tr>
                <tr v-if="filterFields(it.data, getGroupFilter(it.data.key)).length === 0">
                  <td colspan="7" class="empty-row">没有符合条件的字段</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>

        <!-- 单边记录卡 -->
        <div v-else class="only-card">
          <div class="only-head">
            <span :style="`color:${it.kind === 'onlyNew' ? '#2563eb' : '#d97706'};`">
              {{ it.kind === 'onlyNew' ? '＋' : '－' }}
            </span>
            <span class="mono cmp-key">{{ it.data.key }}</span>
            <span class="chip" :class="it.kind === 'onlyNew' ? 'chip-blue' : 'chip-amber'">
              {{ it.kind === 'onlyNew' ? '仅存在于新数据' : '仅存在于旧数据' }}
            </span>
          </div>
          <details class="only-detail">
            <summary>查看记录详情</summary>
            <pre class="only-json scroll-thin">{{ JSON.stringify(it.data.record, null, 2) }}</pre>
          </details>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { exportResult } from '../api'
import { toast } from '../utils/toast.js'

const props = defineProps({
  result: { type: Object, default: null },
  error: { type: String, default: '' },
})

const filters = [
  { value: 'all', label: '全部' },
  { value: 'diff', label: '差异' },
  { value: 'same', label: '一致' },
  { value: 'only', label: '单边' },
]
const filter = ref('all')
const keyword = ref('')

/** 每组（每条记录）的字段过滤状态：key -> 'all' | 'diff' | 'same' */
const groupFilters = [
  { value: 'all', label: '全部' },
  { value: 'diff', label: '差异' },
  { value: 'same', label: '一致' },
]
const groupFilterMap = reactive({})

function getGroupFilter(key) {
  return groupFilterMap[key] || 'all'
}

function setGroupFilter(key, val) {
  groupFilterMap[key] = val
}

function filterFields(comp, mode) {
  if (mode === 'diff') return comp.fields.filter((f) => !f.same)
  if (mode === 'same') return comp.fields.filter((f) => f.same)
  return comp.fields
}

const items = computed(() => {
  if (!props.result) return []
  const kw = keyword.value.trim().toLowerCase()
  const list = []
  if (['all', 'diff', 'same'].includes(filter.value)) {
    props.result.comparisons.forEach((c) => {
      if (filter.value === 'diff' && !c.hasDiff) return
      if (filter.value === 'same' && c.hasDiff) return
      if (kw && !c.key.toLowerCase().includes(kw)) return
      list.push({ kind: 'compare', data: c })
    })
  }
  if (['all', 'only'].includes(filter.value)) {
    props.result.onlyInNew.forEach((r) => {
      if (kw && !r.key.toLowerCase().includes(kw)) return
      list.push({ kind: 'onlyNew', data: r })
    })
    props.result.onlyInOld.forEach((r) => {
      if (kw && !r.key.toLowerCase().includes(kw)) return
      list.push({ kind: 'onlyOld', data: r })
    })
  }
  return list
})

function diffNum(c) { return c.fields.filter((f) => !f.same).length }

function escapeHtml(s) {
  const map = {
    '&': '&' + 'amp;',
    '<': '&' + 'lt;',
    '>': '&' + 'gt;',
    '"': '&' + 'quot;',
    "'": '&' + '#39;',
  }
  return String(s).replace(/[&<>"']/g, (c) => map[c])
}

function formatVal(v) {
  if (v === undefined) return '<span class="hint" style="font-style:italic;">undefined</span>'
  if (v === null) return '<span style="color:#6b7280;font-style:italic;">null</span>'
  if (typeof v === 'string') return `"${escapeHtml(v)}"`
  if (typeof v === 'object') return escapeHtml(JSON.stringify(v))
  return escapeHtml(String(v))
}

async function onExport() {
  if (!props.result) return
  try {
    await exportResult(props.result)
    toast.success('结果已导出')
  } catch (e) {
    toast.error('导出失败：' + (e.message || e))
  }
}
</script>

<style scoped>
.cr-card { margin-top: 16px; }

.cr-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
  padding: 12px 18px; border-bottom: 1px solid var(--border);
}
.cr-title { display: flex; align-items: center; gap: 10px; }
.cr-label { font-size: 14px; font-weight: 600; }
.cr-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.cr-error {
  margin: 12px 18px; padding: 10px 14px;
  background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c;
  border-radius: 6px; font-size: 13px;
}

.cr-stats {
  display: grid; gap: 12px; padding: 16px 18px;
  grid-template-columns: repeat(6, 1fr);
  background: hsl(210 40% 98% / 0.6);
  border-bottom: 1px solid var(--border);
}
@media (max-width: 900px) {
  .cr-stats { grid-template-columns: repeat(3, 1fr); }
}

.cr-body { padding: 16px 18px; display: flex; flex-direction: column; gap: 10px; }

/* 对比卡 */
.cmp-card {
  border: 1px solid var(--border); border-radius: 8px;
  overflow: hidden; background: #fff;
}
.cmp-summary {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px;
  background: hsl(210 40% 98%);
  cursor: pointer; list-style: none;
}
.cmp-summary::-webkit-details-marker { display: none; }
.cmp-summary:hover { background: hsl(210 40% 96%); }
.cmp-summary-left { display: flex; align-items: center; gap: 10px; }
.cmp-key { font-size: 12px; font-weight: 600; }
.cmp-table-wrap { overflow-x: auto; }
details[open] > .cmp-summary .chev { transform: rotate(90deg); }
.chev { transition: transform 0.15s; display: inline-block; }

/* 组内过滤工具栏 */
.cmp-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px;
  padding: 8px 14px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}
.empty-row {
  text-align: center; color: var(--muted); padding: 16px;
  font-size: 12px;
}

/* 单边卡 */
.only-card {
  border: 1px solid var(--border); border-radius: 8px;
  background: #fff; padding: 10px 14px;
}
.only-head { display: flex; align-items: center; gap: 10px; }
.only-detail { margin-top: 6px; font-size: 12px; }
.only-detail summary {
  cursor: pointer; color: var(--muted); padding: 4px 0;
  list-style: none;
}
.only-detail summary::-webkit-details-marker { display: none; }
.only-detail summary:hover { color: var(--fg); }
.only-json {
  font-family: var(--font-mono); font-size: 11.5px;
  background: hsl(210 40% 98%); border: 1px solid var(--border);
  border-radius: 4px; padding: 8px 10px;
  max-height: 240px; overflow: auto;
  margin: 6px 0 0; white-space: pre;
}
</style>