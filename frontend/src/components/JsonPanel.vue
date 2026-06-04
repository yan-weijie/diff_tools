<template>
  <div class="card json-panel">
    <!-- 头部：标识 + Tab 切换 -->
    <div class="jp-head">
      <div class="jp-title">
        <span class="chip" :class="side === 'new' ? 'chip-blue' : 'chip-amber'">
          {{ side === 'new' ? 'NEW' : 'OLD' }}
        </span>
        <span class="jp-label">{{ label }}</span>
        <span class="jp-status" :class="statusClass">{{ statusText }}</span>
      </div>
      <div class="tabs">
        <button class="tab" :class="{ active: view === 'source' }" @click="view = 'source'">源码</button>
        <button class="tab" :class="{ active: view === 'tree' }" @click="switchToTree">可视化</button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="jp-toolbar">
      <button class="btn-ghost" @click="doFormat">⚡ 格式化</button>
      <button class="btn-ghost" @click="doValidate">✓ 校验</button>
      <button class="btn-ghost" @click="doCompress">⇲ 压缩</button>
      <button class="btn-ghost" @click="doCopy">⧉ 复制</button>
      <button class="btn-ghost" @click="doClear">✕ 清空</button>
      <span class="hint" style="margin-left:auto;">{{ rawText.length }} 字符</span>
    </div>

    <!-- 选取模式提示条 -->
    <div v-if="pickMode" class="jp-pick-tip">
      <span>🎯 选取模式：点击下方可视化树中的节点选取 JsonPath</span>
      <span v-if="pickedPath" class="mono pick-tip-path">{{ pickedPath }}</span>
    </div>

    <!-- 内容区 -->
    <div class="jp-body">
      <textarea
        v-show="view === 'source' && !pickMode"
        v-model="rawText"
        @input="onInput"
        class="json-input scroll-thin"
        :placeholder="placeholder"
      />
      <JsonTree
        v-show="view === 'tree' || pickMode"
        :data="parsedData"
        :error="parseError"
        :pickMode="pickMode"
        :selectedPath="pickedPath"
        class="json-tree-wrap"
        @pick="onTreePick"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineExpose, defineProps, defineEmits } from 'vue'
import JsonTree from './JsonTree.vue'
import { toast } from '../utils/toast.js'

const props = defineProps({
  label: { type: String, default: 'JSON' },
  side: { type: String, default: 'new' }, // 'new' | 'old'
  placeholder: { type: String, default: '粘贴 JSON 数据...' },
  /** 父级控制：是否处于"选取路径"模式 */
  pickMode: { type: Boolean, default: false },
  /** 父级回显：当前已选中的路径（用于高亮） */
  pickedPath: { type: String, default: '' },
})

const emit = defineEmits(['pick'])

const rawText = ref('')
const view = ref('source')
const parsedData = ref(undefined)
const parseError = ref('')
const status = ref('idle') // idle | ok | err
const statusMsg = ref('未校验')

const statusText = computed(() => statusMsg.value)
const statusClass = computed(() => ({
  ok: status.value === 'ok',
  err: status.value === 'err',
}))

function setStatus(s, msg) {
  status.value = s
  statusMsg.value = msg
}

function safeParse(text) {
  if (!text || !text.trim()) return { ok: false, error: '内容为空' }
  try {
    return { ok: true, data: JSON.parse(text) }
  } catch (e) {
    const m = /position\s+(\d+)/.exec(e.message)
    let info = e.message
    if (m) {
      const pos = +m[1]
      const before = text.slice(0, pos)
      const line = before.split('\n').length
      const col = pos - before.lastIndexOf('\n')
      info = `第 ${line} 行第 ${col} 列 - ${e.message}`
    }
    return { ok: false, error: info }
  }
}

function onInput() {
  setStatus('idle', '未校验')
}

function doFormat() {
  const r = safeParse(rawText.value)
  if (!r.ok) { setStatus('err', r.error); toast.error(r.error); return }
  rawText.value = JSON.stringify(r.data, null, 2)
  parsedData.value = r.data
  parseError.value = ''
  setStatus('ok', 'JSON 格式正确')
  toast.success('已格式化')
}
function doValidate() {
  const r = safeParse(rawText.value)
  if (!r.ok) { setStatus('err', r.error); toast.error(r.error); return }
  setStatus('ok', 'JSON 格式正确')
  toast.success('JSON 格式正确')
}
function doCompress() {
  const r = safeParse(rawText.value)
  if (!r.ok) { setStatus('err', r.error); toast.error(r.error); return }
  rawText.value = JSON.stringify(r.data)
  setStatus('ok', '已压缩')
  toast.success('已压缩')
}
function doCopy() {
  if (!rawText.value) { toast.error('内容为空'); return }
  navigator.clipboard.writeText(rawText.value).then(() => toast.success('已复制到剪贴板'))
}
function doClear() {
  rawText.value = ''
  parsedData.value = undefined
  parseError.value = ''
  setStatus('idle', '未校验')
}

function refreshParsed() {
  const r = safeParse(rawText.value)
  if (r.ok) { parsedData.value = r.data; parseError.value = '' }
  else { parsedData.value = undefined; parseError.value = r.error }
}

function switchToTree() {
  view.value = 'tree'
  refreshParsed()
}

/** 选取模式开启时自动解析并切到可视化 */
watch(() => props.pickMode, (on) => {
  if (on) {
    refreshParsed()
    view.value = 'tree'
  }
})

function onTreePick(path) {
  emit('pick', path)
}

// 父组件 API：取值 / 设置内容
defineExpose({
  getText: () => rawText.value.trim(),
  setText: (txt) => {
    rawText.value = typeof txt === 'string' ? txt : JSON.stringify(txt, null, 2)
    setStatus('ok', 'JSON 格式正确')
  },
})
</script>

<style scoped>
.json-panel { display: flex; flex-direction: column; min-height: 460px; }

.jp-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-bottom: 1px solid var(--border);
}
.jp-title { display: flex; align-items: center; gap: 10px; }
.jp-label { font-size: 13px; font-weight: 600; }
.jp-status { font-size: 11px; color: var(--muted); }
.jp-status.ok { color: #16a34a; }
.jp-status.err { color: #dc2626; }

.jp-toolbar {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 10px; background: hsl(210 40% 98%);
  border-bottom: 1px solid var(--border);
}

.jp-body {
  position: relative; flex: 1;
  min-height: 360px; height: 420px;
  background: #fff;
}
.json-input {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  padding: 12px; border: 0; outline: none;
  resize: none;
  font-family: var(--font-mono);
  font-size: 12.5px; line-height: 1.6;
  background: #fff;
}
.json-tree-wrap {
  position: absolute; inset: 0;
  height: 100%; overflow: auto;
}

/* 选取模式提示条 */
.jp-pick-tip {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 14px;
  background: #fff7ed;
  color: #9a3412;
  border-bottom: 1px solid #fed7aa;
  font-size: 12px;
}
.pick-tip-path {
  margin-left: auto;
  font-family: var(--font-mono);
  background: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #fed7aa;
  color: #c2410c;
  font-weight: 600;
}
</style>