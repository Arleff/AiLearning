const { request } = require('../../utils/api');
const CAMERA_VIEWS = ['side_view', 'front_view'];
Page({
  data: { videoName: '', sourceVideoUrl: '', cameraViews: CAMERA_VIEWS, selectedCameraView: 'side_view', submitting: false },
  onShow() { this.setData({ user: wx.getStorageSync('mockUser') }); },
  chooseVideo() {
    wx.chooseVideo({ sourceType: ['album', 'camera'], maxDuration: 15, compressed: true, success: ({ tempFilePath, size }) => {
      const parts = tempFilePath.split('/');
      const name = parts[parts.length - 1] || `swing-${Date.now()}.mp4`;
      this.setData({ videoName: `${name} (${Math.round(size / 1024)}KB)`, sourceVideoUrl: tempFilePath });
    }});
  },
  changeCameraView(event) { this.setData({ selectedCameraView: CAMERA_VIEWS[event.detail.value] }); },
  async submitJob() {
    const { user, videoName, sourceVideoUrl, selectedCameraView } = this.data;
    if (!user?.id) return wx.showToast({ title: '请先去我的页面登录', icon: 'none' });
    if (!sourceVideoUrl) return wx.showToast({ title: '请先选择视频', icon: 'none' });
    try {
      this.setData({ submitting: true });
      const ticket = await request({ url: '/api/uploads/presign', method: 'POST', data: { user_id: user.id, filename: videoName } });
      const job = await request({ url: '/api/analysis/jobs', method: 'POST', data: { user_id: user.id, video_name: videoName, source_video_url: ticket.object_url || sourceVideoUrl, camera_view: selectedCameraView } });
      wx.showToast({ title: '任务已创建', icon: 'success' });
      wx.navigateTo({ url: `/pages/result/result?jobId=${job.id}` });
    } catch (error) {
      wx.showToast({ title: '创建任务失败', icon: 'none' }); console.error(error);
    } finally { this.setData({ submitting: false }); }
  },
});
