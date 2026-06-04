<template>
  <!-- 基础类型 -->
  <template v-if="!isContainer">
    <span
      class="tree-node"
      :class="{ 'pick-target': pickMode, 'pick-selected': isSelected }"
      @click.stop="onPick"
    >
      <template v-if="keyName !== null">
        <span class="tok-key">"{{ keyName }}"</span><span class="tok-punc">: </span>
      </template>
      <span v-if="value === null" class="tok-null">null</span>
      <span v-else-if="typeof value === 'boolean'" class="tok-bool">{{ value }}</span>
      <span v-else-if="typeof value === 'number'" class="tok-num">{{ value }}</span>
      <span v-else-if="typeof value === 'string'" class="tok-str">"{{ value }}"</span>
      <span v-if="!isLast" class="tok-punc">,</span>
      <span class="badge-type">{{ typeName }}</span>
    </span>
  </template>

  <!-- 容器（object / array） -->
  <details v-else :open="defaultOpen" class="tree-row tree-node">
    <summary
      :class="{ 'pick-target': pickMode, 'pick-selected': isSelected }"
      @click="onSummaryClick"
    >
      <span class="chev" style="display:inline-block;width:14px;color:#94a3b8;">▶</span>
      <template v-if="keyName !== null">
        <span class="tok-key">"{{ keyName }}"</span><span class="tok-punc">: </span>
      </template>
      <span class="tok-punc">{{ openBracket }}</span>
      <span class="badge-type">{{ typeName }} · {{ count }}</span>
    </summary>
    <div class="tree-children">
      <template v-if="isArray">
        <div v-for="(item, i) in value" :key="i">
          <span style="color:#94a3b8;font-size:11px;margin-right:4px;">{{ i }}:</span>
          <JsonNode
            :value="item"
            :keyName="null"
            :isLast="i === value.length - 1"
            :level="level + 1"
            :pathPrefix="path + '[' + i + ']'"
            :pickMode="pickMode"
            :selectedPath="selectedPath"
            @pick="$emit('pick', $event)"
          />
        </div>
      </template>
      <template v-else>
        <div v-for="(k, i) in keys" :key="k">
          <JsonNode
            :value="value[k]"
            :keyName="k"
            :isLast="i === keys.length - 1"
            :level="level + 1"
            :pathPrefix="path + '.' + k"
            :pickMode="pickMode"
            :selectedPath="selectedPath"
            @pick="$emit('pick', $event)"
          />
        </div>
      </template>
    </div>
    <div>
      <span class="tok-punc">{{ closeBracket }}</span>
      <span v-if="!isLast" class="tok-punc">,</span>
    </div>
  </details>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { default: null },
  keyName: { default: null },
  isLast: { type: Boolean, default: true },
  level: { type: Number, default: 0 },
  /** 当前节点的 JsonPath（由父级传入并累积） */
  pathPrefix: { type: String, default: '$' },
  /** 是否处于选取模式 */
  pickMode: { type: Boolean, default: false },
  /** 当前选中的路径，用于高亮 */
  selectedPath: { type: String, default: '' },
})

const emit = defineEmits(['pick'])

const path = computed(() => props.pathPrefix)
const isSelected = computed(() => props.pickMode && props.selectedPath === path.value)

const isArray = computed(() => Array.isArray(props.value))
const isObject = computed(
  () => props.value && typeof props.value === 'object' && !isArray.value
)
const isContainer = computed(() => isArray.value || isObject.value)
const keys = computed(() => (isObject.value ? Object.keys(props.value) : []))
const count = computed(() => (isArray.value ? props.value.length : keys.value.length))

const typeName = computed(() => {
  const v = props.value
  if (v === null) return 'null'
  if (Array.isArray(v)) return 'array'
  if (typeof v === 'number') return Number.isInteger(v) ? 'int' : 'float'
  if (typeof v === 'object') return 'object'
  return typeof v
})

const openBracket = computed(() => (isArray.value ? '[' : '{'))
const closeBracket = computed(() => (isArray.value ? ']' : '}'))
const defaultOpen = computed(() => props.level < 2)

function onPick() {
  if (!props.pickMode) return
  emit('pick', path.value)
}

/** 容器节点：选取模式下点击 summary 选取路径而不展开/收起 */
function onSummaryClick(e) {
  if (props.pickMode) {
    e.preventDefault()
    emit('pick', path.value)
  }
}
</script>

<style scoped>
.tree-node {
  font-family: var(--font-mono);
  font-size: 12.5px;
}
.tok-key, .tok-str, .tok-num, .tok-bool, .tok-null, .tok-punc, .badge-type {
  font-family: var(--font-mono);
}

/* 选取模式：节点 hover 高亮 */
.pick-target {
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.12s;
}
.pick-target:hover {
  background: #fff7ed;
  outline: 1px dashed #fb923c;
}
.pick-selected,
.pick-selected:hover {
  background: #fed7aa !important;
  outline: 1px solid #ea580c !important;
}
</style>