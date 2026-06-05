/** 示例 JSON 数据，用于一键填充演示 */
export const demoNew = {
  code: '000000',
  message: 'success',
  data: {
    list: [
      { skuId: 67287295489, storeId: '1005517860', shopName: '自营旗舰店', dealPrice: 199.0, status: 1, tags: ['热销', '新品'] },
      { skuId: 67287295490, storeId: '1005517861', shopName: '数码生活馆', dealPrice: 1299.5, status: 1, tags: ['推荐'] },
      { skuId: 67287295491, storeId: '1005517862', shopName: '美食优选', dealPrice: 39.9, status: 0, tags: [] },
      { skuId: 67287295492, storeId: '1005517863', shopName: '家电直供', dealPrice: 4599.0, status: 1, tags: ['分期免息'] },
    ],
  },
}

export const demoOld = {
  code: 200,
  message: 'OK',
  data: {
    dataList: [
      { sku_id: 67287295489, store_id: 1005517860, shop_name: '自营旗舰店', deal_price: 199.0, status: 1 },
      { sku_id: 67287295490, store_id: 1005517861, shop_name: '数码生活馆', deal_price: 1299.0, status: 1 },
      { sku_id: 67287295491, store_id: 1005517862, shop_name: '美食优选', deal_price: 39.9, status: 1 },
      { sku_id: 67287295493, store_id: 1005517864, shop_name: '图书旗舰店', deal_price: 68.0, status: 1 },
    ],
  },
}