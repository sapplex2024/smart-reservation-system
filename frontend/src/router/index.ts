import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ReservationView from '../views/ReservationView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import ReportsView from '../views/ReportsView.vue'
import SettingsView from '../views/SettingsView.vue'
import LogsView from '../views/LogsView.vue'
import LoginView from '../views/LoginView.vue'
import ProfileView from '../views/ProfileView.vue'


import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/reservation',
      name: 'reservation',
      component: ReservationView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/room-management',
      name: 'RoomManagement',
      component: () => import('../views/RoomManagementView.vue')
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView
    },
    {
      path: '/reports',
      name: 'reports',
      component: ReportsView
    },
    {
      path: '/meeting-panel',
      name: 'MeetingPanel',
      component: () => import('../components/MeetingReservationPanel.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    },
    {
      path: '/siliconflow',
      name: 'siliconflow',
      component: () => import('../views/SiliconFlowView.vue')
    },
    {
      path: '/logs',
      name: 'logs',
      component: LogsView
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 定义不需要认证的页面
  const publicPages = ['login', 'chat', 'RoomManagement']
  const requiresAuth = !publicPages.includes(to.name as string)
  
  // 如果访问登录页面且已登录，重定向到首页
  if (to.name === 'login' && authStore.isAuthenticated) {
    next('/')
    return
  }
  
  // 如果访问需要认证的页面但未登录，重定向到登录页
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  next()
})

export default router