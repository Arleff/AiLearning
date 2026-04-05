const BASE_URL = 'http://127.0.0.1:8000';
function request({ url, method = 'GET', data }) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data); return;
        }
        reject(res.data || res.errMsg);
      },
      fail: reject,
    });
  });
}
module.exports = { BASE_URL, request };
