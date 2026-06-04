import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5001',
  timeout: 60000,
})

export function formatJson(text) {
  return api.post('/api/format', { text })
}

export function validateJson(text) {
  return api.post('/api/validate', { text })
}

export function compareJson(params) {
  return api.post('/api/compare', params)
}

export function compareExcel({ fileA, fileB, keyColumns, timeColumn, ignoreColumns, columnAliases }) {
  const form = new FormData()
  form.append('file_a', fileA)
  form.append('file_b', fileB)
  form.append('key_columns', keyColumns || '')
  form.append('time_column', timeColumn || '')
  form.append('ignore_columns', ignoreColumns || '')
  form.append('column_aliases', columnAliases || '')
  return api.post('/api/compare-excel', form)
}

/** 调用后端导出 CSV，触发浏览器下载 */
export async function exportResult(result) {
  const resp = await api.post('/api/export', { result }, { responseType: 'blob' })
  const blob = new Blob([resp.data], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  a.download = `compare-result-${ts}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/** 调用后端导出 Excel 对比结果，触发浏览器下载 */
export async function exportExcelResult(result) {
  const resp = await api.post('/api/export-excel-result', { result }, { responseType: 'blob' })
  const blob = new Blob([resp.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  a.download = `excel-compare-result-${ts}.xlsx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export default api
