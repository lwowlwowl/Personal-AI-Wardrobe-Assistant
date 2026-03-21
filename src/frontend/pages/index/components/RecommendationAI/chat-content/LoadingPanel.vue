<template>
	<view class="loading-premium-card">
		<view class="shimmer-layer"></view>
		<view class="loading-content-center">
			<view class="aura-ring"></view>
			<text class="loading-step-text editorial-text">{{ LOADING_STEPS[loadingStep] }}</text>
			<text class="loading-sub-text">Scanning your wardrobe assets...</text>
		</view>
		<view class="loading-progress-wrap">
			<view class="loading-progress-track">
				<view class="loading-progress-fill" :style="{ width: loadingProgress + '%' }"></view>
			</view>
			<text class="loading-progress-label">{{ loadingProgressPercent }}%</text>
		</view>
		<view class="skeleton-lines">
			<view class="skeleton-line short"></view>
			<view class="skeleton-line long"></view>
			<view class="skeleton-line medium"></view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { LOADING_STEPS } from '../utils/chatContentAdapter.js'

const STEP_INTERVAL_MS = 800
const PROGRESS_TICK_MS = 150

const loadingStep = ref(0)
const loadingProgress = ref(0)
const loadingProgressPercent = computed(() => Math.floor(loadingProgress.value))

let stepTimer = null
let progressTimer = null
let progressStartAt = 0

function clearTimers() {
	if (stepTimer != null) clearInterval(stepTimer)
	if (progressTimer != null) clearInterval(progressTimer)
	stepTimer = null
	progressTimer = null
}

function startStepCarousel() {
	stepTimer = setInterval(() => {
		loadingStep.value = (loadingStep.value + 1) % LOADING_STEPS.length
	}, STEP_INTERVAL_MS)
}

function startFakeProgress() {
	progressStartAt = Date.now()
	progressTimer = setInterval(() => {
		const elapsed = Date.now() - progressStartAt
		let cap = 95
		let factor = 0.08
		let stallChance = 0

		if (elapsed < 650) {
			cap = 22
			factor = 0.16
			stallChance = 0.25
		} else if (elapsed < 1400) {
			cap = 60
			factor = 0.26
			stallChance = 0.08
		} else if (elapsed < 2400) {
			cap = 68
			factor = 0.06
			stallChance = 0.18
		} else if (elapsed < 5200) {
			cap = 88
			factor = 0.035
			stallChance = 0.12
		} else {
			cap = 95
			factor = 0.018
			stallChance = 0.06
		}

		const remaining = cap - loadingProgress.value
		if (remaining > 0.2) {
			if (stallChance > 0 && Math.random() < stallChance) return
			const wobble = 0.75 + 0.25 * Math.sin(elapsed / 230)
			loadingProgress.value += remaining * factor * wobble
			if (loadingProgress.value > cap) loadingProgress.value = cap
		}
	}, PROGRESS_TICK_MS)
}

onMounted(() => {
	loadingStep.value = 0
	loadingProgress.value = 0
	startStepCarousel()
	startFakeProgress()
})

onUnmounted(() => {
	clearTimers()
})

/**
 * Stop timers, snap progress to 100%, then wait for the same 300ms pause the parent used before swapping messages.
 */
function complete() {
	clearTimers()
	loadingProgress.value = 100
	return new Promise((resolve) => setTimeout(resolve, 300))
}

defineExpose({ complete })
</script>

<style scoped>
.loading-premium-card {
	position: relative;
	width: 100%;
	min-height: 400rpx;
	background: rgba(255, 255, 255, 0.4);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border-radius: 40rpx;
	border: 1px solid rgba(255, 255, 255, 0.8);
	overflow: hidden;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.03);
}

.shimmer-layer {
	position: absolute;
	inset: 0;
	background: linear-gradient(
		120deg,
		rgba(255, 255, 255, 0) 0%,
		rgba(255, 255, 255, 0.8) 50%,
		rgba(255, 255, 255, 0) 100%
	);
	background-size: 200% 100%;
	animation: premiumShimmer 2.5s infinite linear;
	z-index: 1;
}

@keyframes premiumShimmer {
	0% { background-position: -200% 0; }
	100% { background-position: 200% 0; }
}

.loading-content-center {
	position: relative;
	z-index: 2;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 16rpx;
}

.aura-ring {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.3) 50%, transparent 70%);
	animation: auraPulse 2.5s ease-in-out infinite;
}

@keyframes auraPulse {
	0%, 100% { transform: scale(1); opacity: 0.6; }
	50% { transform: scale(1.15); opacity: 1; }
}

.editorial-text {
	font-family: "Didot", "Times New Roman", "PingFang SC", serif;
	font-size: 36rpx;
	color: #1D1D1F;
	letter-spacing: 0.05em;
	animation: textBreath 3s ease-in-out infinite;
}

.loading-step-text {
	font-size: 28rpx;
	color: #9D8B70;
	font-family: "Didot", "Times New Roman", "PingFang SC", serif;
	font-weight: 400;
	letter-spacing: 0.04em;
}

.loading-sub-text {
	font-size: 24rpx;
	color: #9D8B70;
	letter-spacing: 0.1em;
	text-transform: uppercase;
	opacity: 0.7;
}

@keyframes textBreath {
	0%, 100% { transform: scale(1); opacity: 0.8; letter-spacing: 0.05em; }
	50% { transform: scale(1.02); opacity: 1; letter-spacing: 0.08em; }
}

.skeleton-lines {
	position: absolute;
	bottom: 60rpx;
	left: 60rpx;
	right: 60rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	opacity: 0.3;
	z-index: 2;
}

.skeleton-line {
	height: 12rpx;
	background: #EAE5D9;
	border-radius: 10rpx;
}

.skeleton-line.short { width: 30%; }
.skeleton-line.long { width: 80%; }
.skeleton-line.medium { width: 60%; }

.loading-progress-wrap {
	position: relative;
	z-index: 2;
	width: 100%;
	padding: 0 60rpx;
	box-sizing: border-box;
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin-top: 32rpx;
}

.loading-progress-track {
	flex: 1;
	height: 6rpx;
	background: rgba(157, 139, 112, 0.15);
	border-radius: 6rpx;
	overflow: hidden;
	position: relative;
}

.loading-progress-fill {
	height: 100%;
	background: linear-gradient(90deg, #9D8B70 0%, #C4B59D 50%, #9D8B70 100%);
	background-size: 200% 100%;
	border-radius: 6rpx;
	transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	animation: gradientFlow 2s linear infinite;
	position: relative;
}

.loading-progress-fill::after {
	content: '';
	position: absolute;
	right: 0;
	top: -2rpx;
	bottom: -2rpx;
	width: 20rpx;
	background: #FFF;
	box-shadow: 0 0 10rpx 4rpx rgba(255, 255, 255, 0.8);
	border-radius: 50%;
	filter: blur(2px);
}

@keyframes gradientFlow {
	0% { background-position: 100% 0; }
	100% { background-position: -100% 0; }
}

.loading-progress-label {
	font-size: 20rpx;
	color: #9D8B70;
	font-variant-numeric: tabular-nums;
	min-width: 56rpx;
	text-align: right;
	font-weight: 500;
}
</style>
