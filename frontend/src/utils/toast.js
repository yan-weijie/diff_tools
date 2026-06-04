/** 极简全局 Toast：调用 toast.success() / toast.error() / toast.info() */
function ensureWrap() {
  let wrap = document.querySelector('.toast-wrap')
  if (!wrap) {
    wrap = document.createElement('div')
    wrap.className = 'toast-wrap'
    document.body.appendChild(wrap)
  }
  return wrap
}

function show(msg, type = 'info', duration = 2400) {
  const wrap = ensureWrap()
  const el = document.createElement('div')
  el.className = `toast ${type}`
  el.textContent = msg
  wrap.appendChild(el)
  setTimeout(() => {
    el.style.transition = 'opacity .2s'
    el.style.opacity = '0'
    setTimeout(() => el.remove(), 200)
  }, duration)
}

export const toast = {
  success: (m, d) => show(m, 'success', d),
  error:   (m, d) => show(m, 'error', d),
  info:    (m, d) => show(m, 'info', d),
}