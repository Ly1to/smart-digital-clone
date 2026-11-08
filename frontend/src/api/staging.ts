import { http } from './http'
import type {
  GithubStatus,
  GithubSyncResult,
  StagedApproveAllResult,
  StagedApproveResult,
  StagedSchedule,
  StagedScheduleInput,
} from '@/types/schedule'

export async function fetchStagedSchedules(): Promise<StagedSchedule[]> {
  const { data } = await http.get<StagedSchedule[]>('/staging')
  return data
}

export async function updateStagedSchedule(
  id: number,
  payload: StagedScheduleInput,
): Promise<StagedSchedule> {
  const { data } = await http.patch<StagedSchedule>(`/staging/${id}`, payload)
  return data
}

export async function approveStagedSchedule(id: number): Promise<StagedApproveResult> {
  const { data } = await http.post<StagedApproveResult>(`/staging/${id}/approve`)
  return data
}

export async function rejectStagedSchedule(id: number): Promise<StagedSchedule> {
  const { data } = await http.post<StagedSchedule>(`/staging/${id}/reject`)
  return data
}

export async function approveAllStagedSchedules(): Promise<StagedApproveAllResult> {
  const { data } = await http.post<StagedApproveAllResult>('/staging/approve-all')
  return data
}

export async function fetchGithubStatus(): Promise<GithubStatus> {
  const { data } = await http.get<GithubStatus>('/auto-sources/github/status')
  return data
}

export async function syncGithub(): Promise<GithubSyncResult> {
  const { data } = await http.post<GithubSyncResult>('/auto-sources/github/sync')
  return data
}

export async function fetchGiteeStatus(): Promise<GithubStatus> {
  const { data } = await http.get<GithubStatus>('/auto-sources/gitee/status')
  return data
}

export async function syncGitee(): Promise<GithubSyncResult> {
  const { data } = await http.post<GithubSyncResult>('/auto-sources/gitee/sync')
  return data
}
