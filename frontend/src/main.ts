import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import { initTheme } from './composables/useTheme'
import { useAuthStore } from './stores/auth'
import 'element-plus/dist/index.css'
import './styles/main.css'
import './styles/calendar.css'

initTheme()

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

window.addEventListener('auth:unauthorized', () => {
  useAuthStore(pinia).clearSession()
  const current = router.currentRoute.value
  if (current.name && current.name !== 'login') {
    void router.replace({
      name: 'login',
      query: current.fullPath !== '/' ? { redirect: current.fullPath } : {},
    })
  }
})

app.mount('#app')
