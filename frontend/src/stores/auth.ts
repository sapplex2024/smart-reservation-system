import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  company_name?: string
  phone?: string
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  
  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  
  // 登录
  const login = async (username: string, password: string) => {
    try {
      loading.value = true
      
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '登录失败')
      }
      
      const data = await response.json()
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      
      // 直接使用返回的用户信息
      if (data.user) {
        user.value = data.user
      } else {
        // 如果没有用户信息，则获取用户信息
        await fetchUserInfo()
      }
      
      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      return { 
        success: false, 
        error: error instanceof Error ? error.message : '登录失败' 
      }
    } finally {
      loading.value = false
    }
  }
  
  // 注册
  const register = async (userData: {
    username: string
    email: string
    full_name: string
    company_name?: string
    phone?: string
    password: string
  }) => {
    try {
      loading.value = true
      
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '注册失败')
      }
      
      const data = await response.json()
      return { success: true, message: data.message }
    } catch (error) {
      console.error('注册失败:', error)
      return { 
        success: false, 
        error: error instanceof Error ? error.message : '注册失败' 
      }
    } finally {
      loading.value = false
    }
  }
  
  // 获取用户信息
  const fetchUserInfo = async () => {
    if (!token.value) return
    
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token 无效，清除登录状态
          logout()
        }
        throw new Error('获取用户信息失败')
      }
      
      const userData = await response.json()
      user.value = userData
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
  
  // 登出
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }
  
  // 初始化时获取用户信息
  const init = async () => {
    // 由于系统已移除认证要求，不再自动获取用户信息
    // 如果需要用户信息，可以手动调用 fetchUserInfo
    return
  }
  
  return {
    // 状态
    token,
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    login,
    register,
    logout,
    fetchUserInfo,
    init
  }
})