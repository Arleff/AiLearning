const { request } = require('../../utils/api');
Page({
  data: { jobId: null, job: null, loading: true },
  onLoad(query) { this.setData({ jobId: query.jobId }); },
  async onShow() { await this.fetchJob(); },
  async fetchJob() {
    const user = wx.getStorageSync('mockUser');
    if (!user?.id || !this.data.jobId) return;
    try { this.setData({ loading: true }); const job = await request({ url: `/api/analysis/jobs/${this.data.jobId}?user_id=${user.id}` }); this.setData({ job }); }
    catch (error) { console.error(error); wx.showToast({ title: '获取结果失败', icon: 'none' }); }
    finally { this.setData({ loading: false }); }
  },
  async paySingle() {
    const user = wx.getStorageSync('mockUser'); const { job } = this.data;
    if (!user?.id || !job?.id) return;
    try {
      const order = await request({ url: '/api/billing/orders', method: 'POST', data: { user_id: user.id, order_type: 'single', amount: 19.9, target_job_id: job.id } });
      await request({ url: `/api/billing/orders/${order.id}/pay`, method: 'POST' });
      wx.showToast({ title: '已解锁', icon: 'success' });
      await this.fetchJob();
    } catch (error) { console.error(error); wx.showToast({ title: '支付失败', icon: 'none' }); }
  },
  refresh() { this.fetchJob(); },
});
