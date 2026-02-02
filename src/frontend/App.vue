<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			// 应用启动时的初始化逻辑
			// 例如：检查登录状态、获取系统信息等
		},
		onShow: function() {
			console.log('App Show')
			// 应用显示时的逻辑
			// 例如：刷新数据、恢复连接等
		},
		onHide: function() {
			console.log('App Hide')
			// 应用隐藏时的逻辑
			// 例如：保存状态、暂停任务等
		}
	}
</script>

<style>
	/* 全局样式 */
	@import './uni.scss';
	
	page {
		background-color: #EBE3D5;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
	}
	
	/* 重置默认样式 */
	* {
		box-sizing: border-box;
	}
	
	/* 移除按钮默认边框 */
	button {
		padding: 0;
		margin: 0;
		background: none;
		border: none;
	}
	
	button::after {
		border: none;
	}
	
	/* 输入框样式 */
	input {
		outline: none;
	}
	
	/* 滚动条样式 */
	::-webkit-scrollbar {
		width: 8rpx;
		height: 8rpx;
	}
	
	::-webkit-scrollbar-thumb {
		background-color: #9B8B6F;
		border-radius: 4rpx;
	}
	
	::-webkit-scrollbar-track {
		background-color: transparent;
	}
</style>
