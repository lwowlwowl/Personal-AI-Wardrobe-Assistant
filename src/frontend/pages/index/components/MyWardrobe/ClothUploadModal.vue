<template>
	<view v-if="visible" class="modal-overlay modal-overlay-enter" @click="handleOverlayClick">
		<view class="modal-box modal-box-enter" @click.stop>
			<view class="modal-header">
				<view class="modal-header-inner">
					<text class="modal-title">Upload item</text>
					<text class="close-btn" @click="close">×</text>
				</view>
				<view class="modal-title-divider"></view>
			</view>

			<view class="modal-content" @click.stop @touchstart.stop>
				<view class="form-group">
					<text class="form-label">Item name</text>
					<input
						type="text"
						class="form-input"
						v-model="form.name"
						placeholder="Enter item name"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">Category</text>
					<view class="category-options">
						<view
							v-for="opt in typeOptions"
							:key="opt.value"
							class="category-option"
							:class="{ active: form.category === opt.value }"
							@click="form.category = opt.value"
						>
							<text>{{ opt.label }}</text>
						</view>
					</view>
				</view>

				<view class="form-group">
					<text class="form-label">SubCategory</text>
					<input
						type="text"
						class="form-input"
						v-model="form.subcategory"
						placeholder="e.g. T-shirt, jeans"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">Color</text>
					<input
						type="text"
						class="form-input"
						v-model="form.color"
						placeholder="e.g. red, navy blue"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">Season</text>
					<view class="season-options">
						<view
							v-for="opt in seasonOptions"
							:key="opt.value"
							class="season-option"
							:class="{ active: form.season === opt.value }"
							@click="form.season = opt.value"
						>
							<text>{{ opt.label }}</text>
						</view>
					</view>
				</view>

				<view class="form-group">
					<text class="form-label">Brand</text>
					<input
						type="text"
						class="form-input"
						v-model="form.brand"
						placeholder="Enter brand"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">Tags (comma-separated)</text>
					<input
						type="text"
						class="form-input"
						v-model="form.tags"
						placeholder="e.g. casual, work"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">Price</text>
					<input
						type="number"
						class="form-input"
						v-model="form.price"
						placeholder="Enter price"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group form-group-optional">
					<text class="form-label">Description</text>
					<textarea
						class="form-textarea"
						v-model="form.description"
						placeholder="Enter description..."
						maxlength="200"
						:adjust-position="true"
					/>
				</view>
			</view>

			<view class="modal-actions">
				<view class="btn-cancel" @click="close">Cancel</view>
				<view class="btn-confirm" @click="submit">Save</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false
	},
	itemId: {
		type: [Number, String],
		default: null
	},
	initialFormData: {
		type: Object,
		default: () => ({
			name: '',
			category: '',
			subcategory: '',
			color: '',
			season: '',
			brand: '',
			tags: '',
			description: '',
			price: ''
		})
	},
	typeOptions: {
		type: Array,
		default: () => []
	},
	seasonOptions: {
		type: Array,
		default: () => []
	}
})

const emit = defineEmits(['update:visible', 'confirm'])

const defaultForm = () => ({
	name: '',
	category: '',
	subcategory: '',
	color: '',
	season: '',
	brand: '',
	tags: '',
	description: '',
	price: ''
})

const form = ref({ ...defaultForm() })

watch(() => props.visible, (v) => {
	if (v && props.initialFormData) {
		form.value = {
			name: props.initialFormData.name ?? '',
			category: props.initialFormData.category ?? '',
			subcategory: props.initialFormData.subcategory ?? '',
			color: props.initialFormData.color ?? '',
			season: props.initialFormData.season ?? '',
			brand: props.initialFormData.brand ?? '',
			tags: props.initialFormData.tags ?? '',
			description: props.initialFormData.description ?? '',
			price: props.initialFormData.price ?? ''
		}
	}
}, { immediate: true })

function handleOverlayClick() {
	emit('update:visible', false)
}

function close() {
	emit('update:visible', false)
}

function submit() {
	if (props.itemId == null) {
		close()
		return
	}
	if (!form.value.category) {
		uni.showToast({ title: 'Please select category', icon: 'none' })
		return
	}
	if (!form.value.name || !String(form.value.name).trim()) {
		uni.showToast({ title: 'Please enter item name', icon: 'none' })
		return
	}
	const seasonVal = form.value.season
	const seasonPayload = seasonVal ? JSON.stringify(Array.isArray(seasonVal) ? seasonVal : [seasonVal]) : undefined
	emit('confirm', {
		itemId: props.itemId,
		payload: {
			name: String(form.value.name).trim(),
			category: form.value.category,
			subcategory: form.value.subcategory || undefined,
			color: form.value.color || undefined,
			season: seasonPayload,
			brand: form.value.brand || undefined,
			tags: form.value.tags || undefined,
			description: form.value.description || undefined,
			price: form.value.price !== '' && form.value.price != null ? form.value.price : undefined
		}
	})
	emit('update:visible', false)
}
</script>

<style scoped>
@keyframes overlayFadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}

@keyframes modalEnter {
	from {
		opacity: 0;
		transform: translateY(-30px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
}

.modal-overlay-enter {
	animation: overlayFadeIn 0.25s ease-out;
}

.modal-box {
	position: relative;
	z-index: 10001;
	width: 90%;
	max-width: 480px;
	max-height: 85vh;
	background: #fff;
	border-radius: 18px;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	box-shadow:
		0 10px 30px rgba(0, 0, 0, 0.12),
		0 4px 12px rgba(0, 0, 0, 0.07);
}

.modal-box-enter {
	animation: modalEnter 0.3s ease-out;
}

.modal-header {
	padding: 28px 28px 0;
	font-weight: bold;
	margin-bottom: 10px;
}

.modal-header-inner {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.modal-title {
	font-size: 18px;
	font-weight: 700;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.close-btn {
	font-size: 28px;
	color: #999;
	cursor: pointer;
	line-height: 1;
	padding: 0 4px;
}

.modal-title-divider {
	height: 1px;
	background: #e8e4dc;
	margin-top: 16px;
}

.modal-content {
	padding: 20px;
	flex: 1;
	overflow-y: auto;
	max-height: calc(85vh - 160px);
	background-color: #f8f8f8;
	margin: 0 20px;
	border-radius: 12px;
}

.form-group {
	margin-bottom: 20px;
}

.form-group:last-child {
	margin-bottom: 0;
}

.form-label {
	display: block;
	font-size: 14px;
	font-weight: 500;
	color: #4f4f4f;
	margin-bottom: 8px;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.form-input {
	width: 100%;
	box-sizing: border-box;
	background-color: #f7f7f7;
	border-radius: 10px;
	border: 1px solid #e1e1e1;
	padding: 12px 16px;
	min-height: 44px;
	font-size: 14px;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	transition: all 0.3s ease;
	position: relative;
	z-index: 2;
	-webkit-user-select: text !important;
	user-select: text !important;
	cursor: text;
}

.form-input:focus {
	background-color: #ffffff;
	border: 1px solid #b89c7a;
	box-shadow: 0 0 10px rgba(184, 156, 122, 0.15);
	outline: none;
}

.form-input::placeholder,
.form-input::-webkit-input-placeholder {
	font-weight: 400;
	color: #999;
}

.form-textarea {
	width: 100%;
	box-sizing: border-box;
	background-color: #f7f7f7;
	border-radius: 10px;
	border: 1px solid #e1e1e1;
	padding: 12px 16px;
	min-height: 90px;
	resize: none;
	font-size: 14px;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	transition: all 0.3s ease;
	position: relative;
	z-index: 2;
	-webkit-user-select: text !important;
	user-select: text !important;
	cursor: text;
}

.form-textarea:focus {
	background-color: #ffffff;
	border: 1px solid #b89c7a;
	box-shadow: 0 0 10px rgba(184, 156, 122, 0.15);
	outline: none;
}

.form-textarea::placeholder,
.form-textarea::-webkit-input-placeholder {
	font-weight: 400;
	color: #999;
}

.category-options {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
}

.category-option {
	padding: 12px 8px;
	border: 1px solid #e1e1e1;
	border-radius: 10px;
	text-align: center;
	cursor: pointer;
	transition: all 0.2s ease;
	font-size: 13px;
	background-color: #f7f7f7;
	color: #4f4f4f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.category-option.active {
	background: #fff9f1;
	border-color: #b89c7a;
	color: #8c7355;
	font-weight: 600;
	box-shadow: 0 0 0 2px rgba(184, 156, 122, 0.2);
}

.season-options {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
}

.season-option {
	padding: 10px 16px;
	border: 1px solid #e1e1e1;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.2s ease;
	font-size: 13px;
	background-color: #f7f7f7;
	color: #4f4f4f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.season-option.active {
	background: #fff9f1;
	border-color: #b89c7a;
	color: #8c7355;
	font-weight: 600;
	box-shadow: 0 0 0 2px rgba(184, 156, 122, 0.2);
}

.modal-actions {
	padding: 28px;
	border-top: 1px solid #e8e4dc;
	display: flex;
	gap: 12px;
}

.btn-cancel,
.btn-confirm {
	flex: 1;
	padding: 14px 28px;
	text-align: center;
	border-radius: 10px;
	font-size: 14px;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.3s ease;
	border: none;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.btn-cancel {
	background: #f1efeb;
	color: #666;
}

.btn-cancel:hover {
	background: #e8e4dc;
}

.btn-cancel:active {
	opacity: 0.9;
}

.btn-confirm {
	background-color: #8c7355;
	color: #fff;
}

.btn-confirm:hover {
	background-color: #9b8162;
	cursor: pointer;
}

.btn-confirm:active {
	background-color: #7a6349;
	opacity: 0.95;
}
</style>
