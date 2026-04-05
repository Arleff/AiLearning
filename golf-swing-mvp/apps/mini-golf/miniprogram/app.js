App({
  globalData: { apiBaseUrl: 'http://127.0.0.1:8000', user: null },
  onLaunch() {
    const user = wx.getStorageSync('mockUser');
    if (user) this.globalData.user = user;
  },
});
