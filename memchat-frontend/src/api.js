// src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

export const sendMessage = (userId, message, history) =>
  api.post('/chat', { user_id: userId, message, history })

export const getMemories = (userId) =>
  api.get(`/memories/${userId}`)

export const deleteMemory = (userId, memoryId) =>
  api.delete(`/memories/${userId}/${memoryId}`)

export const deleteAllMemories = (userId) =>
  api.delete(`/memories/${userId}`)
