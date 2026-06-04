<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="side-brand">
        <div class="brand-logo">⇄</div>
        <div>
          <div class="brand-title">数据对比工具</div>
          <div class="brand-sub">price-qa-skills</div>
        </div>
      </div>

      <nav class="side-nav" aria-label="对比模块">
        <button
          v-for="item in menuItems"
          :key="item.value"
          class="side-item"
          :class="{ active: activeModule === item.value }"
          @click="activeModule = item.value"
        >
          <span class="side-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </aside>

    <section class="main-shell">
      <header class="app-header">
        <div class="content-header">
          <div>
            <h1>{{ currentModule.title }}</h1>
            <div class="sub">{{ currentModule.sub }}</div>
          </div>
          <div v-if="activeModule === 'json'" class="header-actions">
            <button class="btn" @click="loadDemo">✨ 加载示例</button>
            <button class="btn" @click="clearAll">⌫ 清空</button>
          </div>
          <div v-else class="header-actions">
            <button class="btn" @click="clearExcel">⌫ 清空</button>
          </div>
        </div>
      </header>

      <main class="app-content">
        <section v-show="activeModule === 'json'">
          <section class="card" style="padding:16px;">
            <div class="cfg-grid">
              <div>
                <label class="label">新数据 JsonPath</label>
                <div class="path-input">
                  <input v-model="newPath" class="input mono" placeholder="$.data.list" />
                  <button
                    class="btn pick-btn"
                    :class="{ active: pickFor === 'new' }"
                    :title="pickFor === 'new' ? '点击退出选取' : '从新数据可视化树选取路径'"
                    @click="togglePick('new')"
                  >
                    {{ pickFor === 'new' ? '✕ 退出' : '🎯 选取' }}
                  </button>
                </div>
              </div>
              <div>
                <label class="label">旧数据 JsonPath</label>
                <div class="path-input">
                  <input v-model="oldPath" class="input mono" placeholder="$.data.dataList" />
                  <button
                    class="btn pick-btn"
                    :class="{ active: pickFor === 'old' }"
                    :title="pickFor === 'old' ? '点击退出选取' : '从旧数据可视化树选取路径'"
                    @click="togglePick('old')"
                  >
                    {{ pickFor === 'old' ? '✕ 退出' : '🎯 选取' }}
                  </button>
                </div>
              </div>
              <div>
                <label class="label">联合主键</label>
                <input
                  v-model="primaryKey"
                  class="input mono"
                  placeholder="skuId, storeId"
                  title="多字段用逗号/加号/空格分隔，留空则使用默认 skuId+storeId；自动适配 camel/snake 命名"
                />
              </div>
              <div>
                <label class="label">忽略字段</label>
                <input
                  v-model="ignoreFields"
                  class="input mono"
                  placeholder="updateTime, dealPrice"
                  title="多字段用逗号/加号/空格分隔；自动适配 camel/snake 命名和内置字段映射"
                />
              </div>
              <div style="display:flex;align-items:flex-end;">
                <button class="btn btn-primary" style="width:100%;" :disabled="loading" @click="doCompare">
                  {{ loading ? '对比中...' : '⇄ 开始对比' }}
                </button>
              </div>
            </div>
          </section>

          <section class="panels-grid" style="margin-top:16px;">
            <JsonPanel
              ref="newPanel"
              side="new"
              label="新接口数据"
              :pickMode="pickFor === 'new'"
              :pickedPath="pickFor === 'new' ? newPath : ''"
              @pick="onPickedPath('new', $event)"
              placeholder='粘贴新接口返回的 JSON 数据，例如：
{
  "code": "000000",
  "data": { "list": [...] }
}'
            />
            <JsonPanel
              ref="oldPanel"
              side="old"
              label="旧接口数据"
              :pickMode="pickFor === 'old'"
              :pickedPath="pickFor === 'old' ? oldPath : ''"
              @pick="onPickedPath('old', $event)"
              placeholder='粘贴旧接口返回的 JSON 数据，例如：
{
  "code": 200,
  "data": { "dataList": [...] }
}'
            />
          </section>

          <CompareResult :result="compareResult" :error="compareError" />
        </section>

        <section v-show="activeModule === 'excel'" class="excel-module">
          <section class="card excel-config">
            <div class="excel-upload-grid">
              <label class="upload-box">
                <input
                  :key="'file-a-' + excelFileInputKey"
                  type="file"
                  accept=".xlsx,.xls"
                  @change="onExcelFileChange('a', $event)"
                />
                <span class="upload-title">文件A</span>
                <span class="upload-name">{{ fileA ? fileA.name : '选择 Excel 文件' }}</span>
              </label>
              <label class="upload-box">
                <input
                  :key="'file-b-' + excelFileInputKey"
                  type="file"
                  accept=".xlsx,.xls"
                  @change="onExcelFileChange('b', $event)"
                />
                <span class="upload-title">文件B</span>
                <span class="upload-name">{{ fileB ? fileB.name : '选择 Excel 文件' }}</span>
              </label>
            </div>

            <div class="excel-options">
              <div>
                <label class="label">主键列</label>
                <input v-model="excelKeyColumns" class="input mono" placeholder="商品编码, 门店ID" />
              </div>
              <div>
                <label class="label">时间列</label>
                <input v-model="excelTimeColumn" class="input mono" placeholder="时间" />
              </div>
              <div>
                <label class="label">忽略列</label>
                <input v-model="excelIgnoreColumns" class="input mono" placeholder="列名1, 列名2" />
              </div>
              <div>
                <label class="label">列名映射</label>
                <input v-model="excelColumnAliases" class="input mono" placeholder="文件B列=文件A列" />
              </div>
              <div class="excel-submit">
                <button class="btn btn-primary" style="width:100%;" :disabled="excelLoading" @click="doExcelCompare">
                  {{ excelLoading ? '对比中...' : '⇄ 开始对比' }}
                </button>
              </div>
            </div>
          </section>

          <section class="card excel-result">
            <div class="excel-result-head">
              <div>
                <div class="excel-result-title">Excle 对比结果</div>
                <div v-if="excelResult" class="hint">
                  {{ excelResult.totalA }} vs {{ excelResult.totalB }} · 差异 {{ excelResult.diffCount }} / {{ excelResult.commonCount }}
                </div>
                <div v-else class="hint">上传两个文件后展示</div>
              </div>
              <button class="btn" :disabled="!excelResult" @click="onExportExcel">⤓ 导出 Excel</button>
            </div>

            <div v-if="excelError" class="excel-error">⚠ {{ excelError }}</div>

            <div v-if="excelResult" class="excel-stats">
              <div class="stat"><div class="lbl">文件A行数</div><div class="val">{{ excelResult.totalA }}</div></div>
              <div class="stat"><div class="lbl">文件B行数</div><div class="val">{{ excelResult.totalB }}</div></div>
              <div class="stat"><div class="lbl">共同主键</div><div class="val blue">{{ excelResult.commonCount }}</div></div>
              <div class="stat"><div class="lbl">字段差异</div><div class="val red">{{ excelResult.diffCount }}</div></div>
              <div class="stat"><div class="lbl">仅A有</div><div class="val amber">{{ excelResult.onlyA.length }}</div></div>
              <div class="stat"><div class="lbl">仅B有</div><div class="val amber">{{ excelResult.onlyB.length }}</div></div>
            </div>

            <div class="excel-result-body">
              <div v-if="!excelResult && !excelError" class="empty">
                <div class="empty-icon">📦</div>
                <p>暂无 Excle 对比结果</p>
              </div>

              <template v-if="excelResult">
                <div class="excel-section-title">字段值差异</div>
                <div v-if="excelResult.diffRecords.length === 0" class="empty small-empty">
                  共同主键的所有字段值完全一致
                </div>
                <template v-else>
                  <details
                    v-for="record in excelResult.diffRecords"
                    :key="record.key"
                    class="cmp-card"
                  >
                    <summary class="cmp-summary">
                      <div class="cmp-summary-left">
                        <span class="chev" style="color:#94a3b8;">▶</span>
                        <span class="mono cmp-key">{{ record.key }}</span>
                        <span class="chip chip-red">⚠ {{ record.diffCount }} 列差异</span>
                      </div>
                    </summary>
                    <div class="cmp-table-wrap scroll-thin">
                      <table class="compare-table excel-table">
                        <thead>
                          <tr><th>列名</th><th>文件A</th><th>文件B</th></tr>
                        </thead>
                        <tbody>
                          <tr v-for="diff in record.diffs" :key="diff.field" class="diff">
                            <td class="mono">{{ diff.field }}</td>
                            <td class="mono cell-diff">{{ formatExcelCell(diff.a) }}</td>
                            <td class="mono cell-diff">{{ formatExcelCell(diff.b) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </details>
                </template>

                <div class="only-grid">
                  <div class="only-block">
                    <div class="excel-section-title">仅文件A有</div>
                    <details v-for="(row, index) in excelResult.onlyA.slice(0, 20)" :key="index" class="only-card">
                      <summary class="only-head">
                        <span style="color:#2563eb;">＋</span>
                        <span class="mono cmp-key">{{ buildExcelRowKey(row) }}</span>
                      </summary>
                      <pre class="only-json scroll-thin">{{ JSON.stringify(row, null, 2) }}</pre>
                    </details>
                    <div v-if="excelResult.onlyA.length === 0" class="hint">无单边记录</div>
                    <div v-else-if="excelResult.onlyA.length > 20" class="hint">
                      仅预览前 20 条，完整数据请导出 Excel。
                    </div>
                  </div>
                  <div class="only-block">
                    <div class="excel-section-title">仅文件B有</div>
                    <details v-for="(row, index) in excelResult.onlyB.slice(0, 20)" :key="index" class="only-card">
                      <summary class="only-head">
                        <span style="color:#d97706;">－</span>
                        <span class="mono cmp-key">{{ buildExcelRowKey(row) }}</span>
                      </summary>
                      <pre class="only-json scroll-thin">{{ JSON.stringify(row, null, 2) }}</pre>
                    </details>
                    <div v-if="excelResult.onlyB.length === 0" class="hint">无单边记录</div>
                    <div v-else-if="excelResult.onlyB.length > 20" class="hint">
                      仅预览前 20 条，完整数据请导出 Excel。
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </section>
        </section>

        <footer class="app-footer">
          数据对比工具 · sc-parrot-ai / price-qa-skills
        </footer>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import JsonPanel from './components/JsonPanel.vue'
import CompareResult from './components/CompareResult.vue'
import { compareExcel, compareJson, exportExcelResult } from './api'
import { toast } from './utils/toast.js'
import { demoNew, demoOld } from './utils/demoData.js'

const menuItems = [
  { value: 'json', label: 'JSON对比', icon: '{}' },
  { value: 'excel', label: 'Excle对比', icon: 'XLS' },
]
const activeModule = ref('json')
const currentModule = computed(() => (
  activeModule.value === 'json'
    ? { title: 'JSON 数据对比工具', sub: '接口数据一致性验证 · 支持字段映射与联合主键匹配' }
    : { title: 'Excle 数据对比工具', sub: 'LBS 明细文件一致性验证 · 主键匹配与差异导出' }
))

const newPanel = ref(null)
const oldPanel = ref(null)
const newPath = ref('$.data.list')
const oldPath = ref('$.data.dataList')
const primaryKey = ref('skuId, storeId')
const ignoreFields = ref('')
const compareResult = ref(null)
const compareError = ref('')
const loading = ref(false)

/** 'new' | 'old' | null：当前哪个输入框处于选取模式 */
const pickFor = ref(null)

const fileA = ref(null)
const fileB = ref(null)
const excelKeyColumns = ref('商品编码, 门店ID')
const excelTimeColumn = ref('时间')
const excelIgnoreColumns = ref('')
const excelColumnAliases = ref('')
const excelResult = ref(null)
const excelError = ref('')
const excelLoading = ref(false)
const excelFileInputKey = ref(0)

function togglePick(side) {
  if (pickFor.value === side) {
    pickFor.value = null
    return
  }
  const panel = side === 'new' ? newPanel.value : oldPanel.value
  if (!panel.getText()) {
    toast.error(`请先在${side === 'new' ? '新' : '旧'}数据面板输入 JSON`)
    return
  }
  pickFor.value = side
  toast.info(`已开启选取：点击${side === 'new' ? '新' : '旧'}数据可视化树中的节点`)
}

function onPickedPath(side, path) {
  if (side === 'new') newPath.value = path
  else oldPath.value = path
  toast.success(`已选取路径：${path}`)
  pickFor.value = null
}

async function doCompare() {
  const newJson = newPanel.value.getText()
  const oldJson = oldPanel.value.getText()
  if (!newJson || !oldJson) {
    compareError.value = '请先在两侧面板输入 JSON 数据'
    compareResult.value = null
    toast.error('请输入两端 JSON 数据')
    return
  }
  compareError.value = ''
  loading.value = true
  try {
    const { data } = await compareJson({
      new_json: newJson,
      old_json: oldJson,
      new_path: newPath.value,
      old_path: oldPath.value,
      primary_keys: primaryKey.value,
      ignore_fields: ignoreFields.value,
    })
    if (data.ok) {
      compareResult.value = data.result
      toast.success(`对比完成：${data.result.diffCount} 条差异`)
    } else {
      compareResult.value = null
      compareError.value = data.error
      toast.error(data.error)
    }
  } catch (e) {
    compareError.value = '请求失败：' + (e.message || e)
    toast.error('请求失败，请确认后端服务是否启动 (localhost:5000)')
  } finally {
    loading.value = false
  }
}

function loadDemo() {
  newPanel.value.setText(JSON.stringify(demoNew, null, 2))
  oldPanel.value.setText(JSON.stringify(demoOld, null, 2))
  newPath.value = '$.data.list'
  oldPath.value = '$.data.dataList'
  ignoreFields.value = ''
  toast.success('示例数据已加载，可点击 "开始对比"')
}

function clearAll() {
  newPanel.value.setText('')
  oldPanel.value.setText('')
  compareResult.value = null
  compareError.value = ''
  pickFor.value = null
  ignoreFields.value = ''
  toast.info('已清空')
}

function onExcelFileChange(side, event) {
  const file = event.target.files?.[0] || null
  if (side === 'a') fileA.value = file
  else fileB.value = file
}

async function doExcelCompare() {
  if (!fileA.value || !fileB.value) {
    excelError.value = '请先上传文件A和文件B'
    excelResult.value = null
    toast.error('请上传两个 Excel 文件')
    return
  }
  excelError.value = ''
  excelLoading.value = true
  try {
    const { data } = await compareExcel({
      fileA: fileA.value,
      fileB: fileB.value,
      keyColumns: excelKeyColumns.value,
      timeColumn: excelTimeColumn.value,
      ignoreColumns: excelIgnoreColumns.value,
      columnAliases: excelColumnAliases.value,
    })
    if (data.ok) {
      excelResult.value = data.result
      toast.success(`Excel 对比完成：${data.result.diffCount} 条主键存在字段差异`)
    } else {
      excelResult.value = null
      excelError.value = data.error
      toast.error(data.error)
    }
  } catch (e) {
    excelError.value = '请求失败：' + (e.message || e)
    toast.error('请求失败，请确认后端服务是否启动 (localhost:5000)')
  } finally {
    excelLoading.value = false
  }
}

async function onExportExcel() {
  if (!excelResult.value) return
  try {
    await exportExcelResult(excelResult.value)
    toast.success('Excel 结果已导出')
  } catch (e) {
    toast.error('导出失败：' + (e.message || e))
  }
}

function clearExcel() {
  fileA.value = null
  fileB.value = null
  excelFileInputKey.value += 1
  excelResult.value = null
  excelError.value = ''
  excelIgnoreColumns.value = ''
  excelColumnAliases.value = ''
  toast.info('已清空')
}

function buildExcelRowKey(row) {
  const keys = excelResult.value?.keyColumns || []
  const vals = keys.map((key) => row[key]).filter((val) => val !== undefined && val !== '')
  return vals.length ? vals.join(' / ') : '未识别主键'
}

function formatExcelCell(value) {
  if (value === null || value === undefined) return ''
  return String(value)
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 14px;
  background: #0f172a;
  color: #e2e8f0;
  border-right: 1px solid #1e293b;
}

.side-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 4px 18px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.brand-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.brand-sub {
  font-size: 11px;
  color: #94a3b8;
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.side-item {
  width: 100%;
  height: 38px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.side-item:hover {
  background: #1e293b;
}

.side-item.active {
  background: #ffffff;
  color: #0f172a;
  border-color: #ffffff;
}

.side-icon {
  width: 28px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}

.main-shell {
  min-width: 0;
}

header.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}

.content-header {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 24px;
}

.content-header h1 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.2;
}

.content-header .sub {
  margin-top: 3px;
  font-size: 11px;
  color: var(--muted);
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.app-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px 24px 32px;
}

.cfg-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) minmax(220px, 1.4fr) minmax(170px, 0.9fr) minmax(170px, 0.9fr) minmax(130px, 0.7fr);
  gap: 14px;
  align-items: end;
}

.panels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.path-input {
  display: flex;
  gap: 6px;
}

.path-input .input {
  flex: 1;
}

.pick-btn {
  flex-shrink: 0;
  height: 36px;
}

.pick-btn.active {
  background: #fb923c;
  color: #fff;
  border-color: #fb923c;
}

.pick-btn.active:hover {
  background: #f97316;
  border-color: #f97316;
}

.excel-module {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.excel-config {
  padding: 16px;
}

.excel-upload-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.upload-box {
  min-height: 92px;
  padding: 16px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.upload-box:hover {
  border-color: var(--primary);
  background: #ffffff;
}

.upload-box input {
  display: none;
}

.upload-title {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
}

.upload-name {
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.excel-options {
  margin-top: 14px;
  display: grid;
  grid-template-columns: minmax(160px, 0.9fr) minmax(120px, 0.6fr) minmax(160px, 0.9fr) minmax(220px, 1.1fr) minmax(130px, 0.6fr);
  gap: 14px;
  align-items: end;
}

.excel-submit {
  display: flex;
  align-items: flex-end;
}

.excel-result {
  overflow: hidden;
}

.excel-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border);
}

.excel-result-title {
  font-size: 14px;
  font-weight: 600;
}

.excel-error {
  margin: 12px 18px;
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  border-radius: 6px;
  font-size: 13px;
}

.excel-stats {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
  grid-template-columns: repeat(6, 1fr);
  background: hsl(210 40% 98% / 0.6);
  border-bottom: 1px solid var(--border);
}

.excel-result-body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.excel-section-title {
  font-size: 13px;
  font-weight: 600;
  margin: 4px 0 2px;
}

.cmp-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.cmp-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: hsl(210 40% 98%);
  cursor: pointer;
  list-style: none;
}

.cmp-summary::-webkit-details-marker {
  display: none;
}

.cmp-summary:hover {
  background: hsl(210 40% 96%);
}

.cmp-summary-left,
.only-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cmp-key {
  font-size: 12px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.cmp-table-wrap {
  overflow-x: auto;
}

details[open] > .cmp-summary .chev {
  transform: rotate(90deg);
}

.chev {
  transition: transform 0.15s;
  display: inline-block;
}

.small-empty {
  padding: 18px 12px;
}

.excel-table th:nth-child(1) { width: 22%; }
.excel-table th:nth-child(2),
.excel-table th:nth-child(3) { width: 39%; }

.only-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.only-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.only-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  padding: 10px 14px;
}

.only-card > summary {
  cursor: pointer;
  list-style: none;
}

.only-card > summary::-webkit-details-marker {
  display: none;
}

.only-json {
  font-family: var(--font-mono);
  font-size: 11.5px;
  background: hsl(210 40% 98%);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px 10px;
  max-height: 240px;
  overflow: auto;
  margin: 8px 0 0;
  white-space: pre;
}

.app-footer {
  text-align: center;
  color: var(--muted);
  font-size: 11.5px;
  padding: 20px 0 0;
}

@media (max-width: 1100px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    height: auto;
  }

  .side-nav {
    flex-direction: row;
  }

  .side-item {
    width: auto;
    min-width: 128px;
  }

  .panels-grid,
  .only-grid {
    grid-template-columns: 1fr;
  }

  .excel-options {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .cfg-grid,
  .excel-upload-grid,
  .excel-options {
    grid-template-columns: 1fr;
  }

  .excel-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
