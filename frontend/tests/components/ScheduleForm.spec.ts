import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import dayjs from 'dayjs'
import { describe, expect, it } from 'vitest'

import ScheduleForm from '@/components/schedule/ScheduleForm.vue'
import type { Schedule } from '@/types/schedule'

function makeSchedule(overrides: Partial<Schedule> = {}): Schedule {
  return {
    id: 7,
    title: '项目周会',
    category: 'work',
    description: '讨论进度',
    start_at: '2026-11-05T06:00:00Z',
    end_at: '2026-11-05T07:00:00Z',
    all_day: false,
    location: '线上',
    status: 'pending',
    created_at: '2026-11-01T00:00:00Z',
    updated_at: '2026-11-01T00:00:00Z',
    ...overrides,
  }
}

function mountForm(props: Record<string, unknown> = {}) {
  return mount(ScheduleForm, {
    props,
    global: {
      plugins: [ElementPlus],
    },
  })
}

function findButton(wrapper: ReturnType<typeof mountForm>, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text().includes(text))
  if (!button) {
    throw new Error(`button not found: ${text}`)
  }
  return button
}

async function waitForValidation() {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 150))
  await flushPromises()
}

describe('ScheduleForm', () => {
  it('renders the three fixed category cards', () => {
    const wrapper = mountForm()

    const cards = wrapper.findAll('.category-card')
    expect(cards).toHaveLength(3)
    const labels = cards.map((card) => card.text()).join(' ')
    expect(labels).toContain('工作')
    expect(labels).toContain('外出')
    expect(labels).toContain('私人时间')
  })

  it('does not submit when the title is blank', async () => {
    const wrapper = mountForm()

    await findButton(wrapper, '保存').trigger('click')
    await waitForValidation()

    expect(wrapper.emitted('submit')).toBeUndefined()
    expect(wrapper.text()).toContain('请输入日程标题')
  })

  it('prefills an existing schedule for editing', () => {
    const wrapper = mountForm({ initial: makeSchedule() })

    const titleInput = wrapper.find('input[placeholder="例如：项目周会"]')
    expect((titleInput.element as HTMLInputElement).value).toBe('项目周会')

    const activeCategory = wrapper.find('.category-card.is-active')
    expect(activeCategory.text()).toContain('工作')

    const startInput = wrapper.find('input[placeholder="开始时间"]')
    expect((startInput.element as HTMLInputElement).value).toBe(
      dayjs('2026-11-05T06:00:00Z').format('YYYY-MM-DD HH:mm'),
    )
  })

  it('emits a normalized payload after valid input', async () => {
    const wrapper = mountForm()

    await wrapper.find('input[placeholder="例如：项目周会"]').setValue('  听音乐  ')
    const outingCard = wrapper
      .findAll('.category-card')
      .find((item) => item.text().includes('外出'))
    expect(outingCard).toBeTruthy()
    await outingCard!.trigger('click')

    await findButton(wrapper, '保存').trigger('click')
    await flushPromises()

    const emitted = wrapper.emitted('submit')
    expect(emitted).toBeTruthy()
    expect(emitted![0][0]).toMatchObject({
      title: '听音乐',
      category: 'outing',
      all_day: false,
      status: 'pending',
      description: null,
      location: null,
    })
  })

  it('switches to date pickers for all-day events', async () => {
    const wrapper = mountForm()

    await wrapper.find('.el-switch input').setValue(true)

    expect(wrapper.find('input[placeholder="开始日期"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="结束日期"]').exists()).toBe(true)
  })

  it('reports dirty state when fields change', async () => {
    const wrapper = mountForm()

    await wrapper.find('input[placeholder="例如：项目周会"]').setValue('脏表单')

    const events = wrapper.emitted('dirtyChange')
    expect(events).toBeTruthy()
    expect(events![events!.length - 1]).toEqual([true])
  })

  it('shows an API error banner above the form', () => {
    const wrapper = mountForm({ submitError: '后端保存失败' })

    expect(wrapper.text()).toContain('后端保存失败')
  })

  it('cancels without submitting', async () => {
    const wrapper = mountForm()

    await findButton(wrapper, '取消').trigger('click')

    expect(wrapper.emitted('cancel')).toHaveLength(1)
    expect(wrapper.emitted('submit')).toBeUndefined()
  })
})
