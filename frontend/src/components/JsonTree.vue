<template>
  <div v-if="error" class="tree-error">
    <span style="color:#dc2626;">⚠ 无法解析 JSON：{{ error }}</span>
  </div>
  <div v-else-if="data === undefined || data === null" class="tree-empty">
    粘贴 JSON 并点击 <b>格式化</b> 或切换 <b>可视化</b> 查看结构
  </div>
  <div v-else class="tree-wrap scroll-thin">
    <JsonNode
      :value="data"
      :keyName="null"
      :isLast="true"
      :level="0"
      pathPrefix="$"
      :pickMode="pickMode"
      :selectedPath="selectedPath"
      @pick="$emit('pick', $event)"
    />
  </div>
</template>

<script setup>
import JsonNode from './JsonNode.vue'
defineProps({
  data: { default: undefined },
  error: { type: String, default: '' },
  pickMode: { type: Boolean, default: false },
  selectedPath: { type: String, default: '' },
})
defineEmits(['pick'])
</script>

<style scoped>
.tree-wrap {
  padding: 8px 12px;
  height: 100%;
  overflow: auto;
  background: #fff;
}
.tree-empty {
  padding: 20px; color: var(--muted); font-size: 12.5px; text-align: center;
}
.tree-error {
  padding: 12px; font-family: var(--font-mono); font-size: 12px;
  background: #fef2f2; border-bottom: 1px solid #fecaca;
}
</style>