import { http } from './http'
import type { Schedule, ScheduleInput, ScheduleQuery } from '@/types/schedule'

export async function fetchSchedules(params: ScheduleQuery = {}): Promise<Schedule[]> {
  const { data } = await http.get<Schedule[]>('/schedules', { params })
  return data
}

export async function fetchSchedule(id: number): Promise<Schedule> {
  const { data } = await http.get<Schedule>(`/schedules/${id}`)
  return data
}

export async function createSchedule(payload: ScheduleInput): Promise<Schedule> {
  const { data } = await http.post<Schedule>('/schedules', payload)
  return data
}

export async function updateSchedule(id: number, payload: ScheduleInput): Promise<Schedule> {
  const { data } = await http.patch<Schedule>(`/schedules/${id}`, payload)
  return data
}

export async function deleteSchedule(id: number): Promise<void> {
  await http.delete(`/schedules/${id}`)
}
