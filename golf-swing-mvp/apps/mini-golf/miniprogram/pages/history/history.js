const { request } = require('../../utils/api');
Page({
  data: { jobs: [], loading: false },
  async onShow() {
    const user = wx.getStorageSync('mockUser');
    if (!user?.id) return this.setData({ jobs: [] });
    try { this.setData({ loading: true }); const jobs = await request({ url: `/api/analysis/jobs?user_id=${user.id}` }); this.setData({ jobs }); }
    catch (error) { console.error(error); }
    finally { this.setData({ loading: false }); }
  },
  openJob(event) { wx.navigateTo({ url: `/pages/result/result?jobId=${event.currentTarget.dataset.jobId}` }); },
});
