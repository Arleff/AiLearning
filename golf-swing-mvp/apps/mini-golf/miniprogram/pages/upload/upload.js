const { request } = require('../../utils/api');
const CAMERA_VIEWS = ['side_view', 'front_view'];

function uploadVideo(url, filePath, formData) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url,
      filePath,
      name: 'file',
      formData,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data));
          return;
        }
        reject(res);
      },
      fail: reject,
    });
  });
}

Page({
  data: { videoName: '', sourceVideoUrl: '', originalVideoName: '', cameraViews: CAMERA_VIEWS, selectedCameraView: 'side_view', submitting: false },
  onShow() { this.setData({ user: wx.getStorageSync('mockUser') }); },
  chooseVideo() {
    wx.chooseVideo({ sourceType: ['album', 'camera'], maxDuration: 15, compressed: true, success: ({ tempFilePath, size }) => {
      const parts = tempFilePath.split('/');
      const name = parts[parts.length - 1] || `swing-${Date.now()}.mp4`;
      this.setData({ videoName: `${name} (${Math.round(size / 1024)}KB)`, originalVideoName: name, sourceVideoUrl: tempFilePath });
    }});
  },
  changeCameraView(event) { this.setData({ selectedCameraView: CAMERA_VIEWS[event.detail.value] }); },
  async submitJob() {
    const { user, videoName, originalVideoName, sourceVideoUrl, selectedCameraView } = this.data;
    if (!user?.id) return wx.showToast({ title: '请先去我的页面登录', icon: 'none' });
    if (!sourceVideoUrl) return wx.showToast({ title: '请先选择视频', icon: 'none' });
    try {
      this.setData({ submitting: true });
      const uploadBaseUrl = getApp().globalData.apiBaseUrl || 'http://127.0.0.1:8000';
      const uploadResult = await uploadVideo(`${uploadBaseUrl}/api/uploads/video`, sourceVideoUrl, {
        user_id: String(user.id),
        camera_view: selectedCameraView,
      });
      const job = await request({
        url: '/api/analysis/jobs',
        method: 'POST',
        data: {
          user_id: user.id,
          video_name: originalVideoName || videoName,
          source_video_url: uploadResult.object_url,
          camera_view: selectedCameraView,
        },
      });
      wx.showToast({ title: '任务已创建', icon: 'success' });
      wx.navigateTo({ url: `/pages/result/result?jobId=${job.id}` });
    } catch (error) {
      wx.showToast({ title: '创建任务失败', icon: 'none' }); console.error(error);
    } finally { this.setData({ submitting: false }); }
  },
});
