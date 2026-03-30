<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			// Initialization when the app launches
			// e.g. check login state, read system info
		},
		onShow: function() {
			console.log('App Show')
			// Logic when the app becomes visible
			// e.g. refresh data, resume connections
		},
		onHide: function() {
			console.log('App Hide')
			// Logic when the app goes to background
			// e.g. persist state, pause tasks
		}
	}
</script>

<style>
	/* Global styles */
	@import './uni.scss';
	
	page {
		background-color: #EBE3D5;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
	}
	
	/* Reset default styles */
	* {
		box-sizing: border-box;
	}
	
	/* Remove default button chrome */
	button {
		padding: 0;
		margin: 0;
		background: none;
		border: none;
	}
	
	button::after {
		border: none;
	}
	
	/* Input focus outline */
	input {
		outline: none;
	}
	
	/* Scrollbar */
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
