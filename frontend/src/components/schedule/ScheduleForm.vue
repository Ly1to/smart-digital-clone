<script setup lang="ts">
import { onMounted, nextTick, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules, InputInstance } from 'element-plus'

import { ALL_CATEGORIES, ALL_STATUSES, CATEGORY_META, STATUS_META } from '@/constants/schedule'
import type { Schedule, ScheduleCategory, ScheduleInput } from '@/types/schedule'
import {
  buildSchedulePayload,
  createEmptyFormState,
  formStateFromSchedule,
  isTimeRangeValid,
  serializeFormState,
  type ScheduleFormState,
} from '@/utils/scheduleForm'
import { getErrorMessage } from '@/utils/error'

const props = withDefaults(
  defineProps<{
    initial?: Schedule | null
    initialStart?: string | null
    initialEnd?: string | null
    submitting?: boolean
    submitError?: string
    submitLabel?: string
  }>(),
  {
    initial: null,
    initialStart: null,
    initialEnd: null,
    submitting: false,
    submitError: '',
    submitLabel: '保存',
  },
)

const emit = defineEmits<{
  submit: [payload: ScheduleInput]
  cancel: []
  dirtyChange: [dirty: boolean]
}>()

const formRef = ref<FormInstance>()
const titleInputRef = ref<InputInstance>()
const timeError = ref('')
const form = reactive<ScheduleFormState>(
  props.initial
    ? formStateFromSchedule(props.initial)
    : createEmptyFormState(props.initialStart, props.initialEnd),
)
const initialSnapshot = ref(serializeFormState(form))

const rules: FormRules = {
  title: [
    { required: true, message: '请输入日程标题', trigger: 'change' },
    {
      validator: (_rule, value: string, callback) => {
        if (!value || !value.trim()) {
          callback(new Error('标题不能为空'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
  category: [{ required: true, message: '请选择日程分类', trigger: 'change' }],
  startAt: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endAt: [
    {
      validator: (_rule, _value: string, callback) => {
        if (!form.endAt) {
          callback(new Error('请选择结束时间'))
          return
        }
        if (!isTimeRangeValid(form)) {
          callback(new Error('结束时间必须晚于开始时间'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
  startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  endDate: [
    {
      validator: (_rule, _value: string, callback) => {
        if (!form.endDate) {
          callback(new Error('请选择结束日期'))
          return
        }
        if (!isTimeRangeValid(form)) {
          callback(new Error('结束日期不能早于开始日期'))
          return
        }
        callback()
      },
      trigger: 'change',
    },
  ],
}

onMounted(async () => {
  await nextTick()
  titleInputRef.value?.focus()
})

watch(
  form,
  () => {
    emit('dirtyChange', serializeFormState(form) !== initialSnapshot.value)
  },
  { deep: true },
)

watch(
  () => form.allDay,
  (enabled) => {
    timeError.value = ''
    if (enabled) {
      form.startDate = form.startAt.slice(0, 10)
      form.endDate = form.endAt.slice(0, 10)
      return
    }
    if (form.startDate) {
      form.startAt = `${form.startDate}T09:00:00`
    }
    if (form.endDate) {
      form.endAt = `${form.endDate}T10:00:00`
    }
  },
)

async function selectCategory(category: ScheduleCategory) {
  form.category = category
  await nextTick()
  await formRef.value?.validateField('category').catch(() => false)
}

async function handleSubmit() {
  timeError.value = ''
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }
  if (!isTimeRangeValid(form)) {
    timeError.value = form.allDay ? '结束日期不能早于开始日期' : '结束时间必须晚于开始时间'
    return
  }

  try {
    emit('submit', buildSchedulePayload(form))
  } catch (error) {
    timeError.value = getErrorMessage(error)
  }
}
</script>

<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    class="schedule-form"
    @submit.prevent="handleSubmit"
  >
    <el-alert
      v-if="props.submitError"
      :title="props.submitError"
      type="error"
      show-icon
      :closable="false"
      class="schedule-form__banner"
    />

    <el-form-item label="标题" prop="title">
      <el-input
        ref="titleInputRef"
        v-model="form.title"
        maxlength="200"
        show-word-limit
        placeholder="例如：项目周会"
      />
    </el-form-item>

    <el-form-item label="分类" prop="category">
      <div class="category-cards" role="radiogroup" aria-label="日程分类">
        <button
          v-for="category in ALL_CATEGORIES"
          :key="category"
          type="button"
          role="radio"
          class="category-card"
          :class="{ 'is-active': form.category === category }"
          :aria-checked="form.category === category"
          :style="
            form.category === category
              ? {
                  color: CATEGORY_META[category].color,
                  borderColor: CATEGORY_META[category].color,
                  backgroundColor: CATEGORY_META[category].softColor,
                }
              : undefined
          "
          @click="selectCategory(category)"
        >
          <span
            class="category-card__mark"
            :style="{
              color: CATEGORY_META[category].color,
              backgroundColor: CATEGORY_META[category].softColor,
            }"
            aria-hidden="true"
          >
            {{ CATEGORY_META[category].shortLabel }}
          </span>
          <span>{{ CATEGORY_META[category].label }}</span>
        </button>
      </div>
    </el-form-item>

    <div class="time-grid">
      <el-form-item
        :label="form.allDay ? '开始日期' : '开始时间'"
        :prop="form.allDay ? 'startDate' : 'startAt'"
      >
        <el-date-picker
          v-if="form.allDay"
          v-model="form.startDate"
          type="date"
          value-format="YYYY-MM-DD"
          format="YYYY-MM-DD"
          placeholder="开始日期"
          class="full-width"
        />
        <el-date-picker
          v-else
          v-model="form.startAt"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          format="YYYY-MM-DD HH:mm"
          placeholder="开始时间"
          class="full-width"
        />
      </el-form-item>

      <el-form-item
        :label="form.allDay ? '结束日期' : '结束时间'"
        :prop="form.allDay ? 'endDate' : 'endAt'"
      >
        <el-date-picker
          v-if="form.allDay"
          v-model="form.endDate"
          type="date"
          value-format="YYYY-MM-DD"
          format="YYYY-MM-DD"
          placeholder="结束日期"
          class="full-width"
        />
        <el-date-picker
          v-else
          v-model="form.endAt"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          format="YYYY-MM-DD HH:mm"
          placeholder="结束时间"
          class="full-width"
        />
        <p v-if="timeError" class="schedule-form__error" role="alert">{{ timeError }}</p>
      </el-form-item>
    </div>

    <el-form-item label="全天">
      <div class="switch-row">
        <el-switch v-model="form.allDay" active-text="全天事件" />
        <span class="switch-row__hint">开启后按日期保存，首尾日期都包含</span>
      </div>
    </el-form-item>

    <el-form-item label="地点">
      <el-input
        v-model="form.location"
        maxlength="200"
        placeholder="可选，例如：线上 / 公司会议室"
      />
    </el-form-item>

    <el-form-item label="状态">
      <el-select v-model="form.status" class="status-select">
        <el-option
          v-for="status in ALL_STATUSES"
          :key="status"
          :label="STATUS_META[status].label"
          :value="status"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="描述">
      <el-input
        v-model="form.description"
        type="textarea"
        :rows="4"
        maxlength="5000"
        show-word-limit
        placeholder="可选，填写日程详情"
      />
    </el-form-item>

    <div class="form-actions">
      <el-button @click="emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="props.submitting" @click="handleSubmit">
        {{ props.submitLabel }}
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.schedule-form {
  padding: 4px 0 8px;
}

.schedule-form__banner {
  margin-bottom: 16px;
}

.category-cards {
  display: flex;
  gap: 8px;
  width: 100%;
}

.category-card {
  display: flex;
  flex: 1;
  gap: 7px;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 6px 8px;
  color: var(--color-ink-secondary);
  font-size: 13px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: 9px;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease;
}

.category-card:hover {
  border-color: var(--color-line-strong);
}

.category-card.is-active {
  font-weight: 500;
}

.category-card:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.category-card__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 5px;
}

.time-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0;
}

.full-width {
  width: 100%;
}

:deep(.el-date-editor.full-width) {
  width: 100% !important;
}

.schedule-form__error {
  width: 100%;
  margin: 4px 0 0;
  color: var(--color-danger);
  font-size: 12px;
  line-height: 1.4;
}

.switch-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  align-items: center;
}

.switch-row__hint {
  color: var(--color-ink-muted);
  font-size: 11px;
}

.status-select {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
}

:deep(.el-form-item__label) {
  color: var(--color-ink-secondary);
  font-size: 12px;
  font-weight: 500;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper) {
  background: var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-line) inset;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus),
:deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--color-focus) inset;
}

@media (max-width: 600px) {
  .category-cards {
    flex-direction: column;
  }

  .category-card {
    justify-content: flex-start;
    min-height: 48px;
  }
}
</style>
