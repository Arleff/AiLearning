const { request } = require('../../utils/api');
Page({
  data: { user: null, subscription: null },
  async onShow() {
    const user = wx.getStorageSync('mockUser');
    if (user?.id) { this.setData({ user }); await this.fetchSubscription(user.id); }
  },
  async login() {
    try {
      const profile = await request({ url: '/api/auth/mock-login', method: 'POST', data: { code: `mock-code-${Date.now()}`, nickname: `球友${Date.now().toString().slice(-4)}` } });
      wx.setStorageSync('mockUser', profile);
      this.setData({ user: profile });
      wx.showToast({ title: '登录成功', icon: 'success' });
      await this.fetchSubscription(profile.id);
    } catch (error) { wx.showToast({ title: '登录失败', icon: 'none' }); console.error(error); }
  },
  async fetchSubscription(userId) {
    try { const subscription = await request({ url: `/api/billing/subscription/${userId}` }); this.setData({ subscription }); }
    catch (error) { console.error(error); }
  },
  async buyMembership() {
    const { user } = this.data;
    if (!user?.id) return wx.showToast({ title: '请先登录', icon: 'none' });
    try {
      const order = await request({ url: '/api/billing/orders', method: 'POST', data: { user_id: user.id, order_type: 'subscription', amount: 69.9, plan_type: 'monthly', plan_days: 30 } });
      await request({ url: `/api/billing/orders/${order.id}/pay`, method: 'POST' });
      wx.showToast({ title: '会员已开通', icon: 'success' });
      await this.fetchSubscription(user.id);
    } catch (error) { wx.showToast({ title: '购买失败', icon: 'none' }); console.error(error); }
  },
});
