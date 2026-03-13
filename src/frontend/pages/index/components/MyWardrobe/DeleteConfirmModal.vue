<template>
  <view v-if="visible" class="modal-overlay" @click.self="handleCancel">
    <view class="modal">
      <text class="title">{{ title }}</text>
      <text class="content">{{ content }}</text>
      <view class="actions">
        <view class="btn cancel-btn" @click="handleCancel">Cancel</view>
        <view class="btn danger" @click="handleConfirm">Delete</view>
      </view>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Delete item'
  },
  content: {
    type: String,
    default: "Are you sure you want to delete this clothing item? \nThis action cannot be undone."
  }
})

const emit = defineEmits(['confirm', 'cancel'])

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.modal {
  width: 420px;
  max-width: 90vw;
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
  display: block;
}

.content {
  color: #666;
  margin-top: 10px;
  font-size: 16px;
  line-height: 1.5;
  display: block;
  white-space: pre-line;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.btn:active {
  opacity: 0.9;
  transform: scale(0.98);
}

.cancel-btn {
  background: #f3f1ec;
  color: #1d1d1f;
}

.danger {
  background: #e74c3c;
  color: white;
}
</style>
