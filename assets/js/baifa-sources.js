window.baifaSourceOrder = [
  '《百法直解》',
  '《成唯识论》',
  '《大乘五蕴论》',
  '《大乘广五蕴论》',
  '《大乘阿毘达磨集论》',
  '《显扬圣教论》',
];

window.baifaGetSourceRank = function (title) {
  const order = window.baifaSourceOrder || [];
  if (!title) {
    return order.length + 1;
  }
  for (let i = 0; i < order.length; i += 1) {
    if (title.startsWith(order[i])) {
      return i;
    }
  }
  return order.length + 1;
};

window.baifaSortSourceTitles = function (titles) {
  const list = Array.isArray(titles) ? titles.slice() : [];
  return list
    .map((title, index) => ({ title, index }))
    .sort((a, b) => {
      const rankDiff = window.baifaGetSourceRank(a.title) - window.baifaGetSourceRank(b.title);
      return rankDiff || a.index - b.index;
    })
    .map((entry) => entry.title);
};

window.baifaSortSources = function (sources) {
  const list = Array.isArray(sources) ? sources.slice() : [];
  return list
    .map((source, index) => ({ source, index }))
    .sort((a, b) => {
      const rankDiff = window.baifaGetSourceRank(a.source && a.source.title) -
        window.baifaGetSourceRank(b.source && b.source.title);
      return rankDiff || a.index - b.index;
    })
    .map((entry) => entry.source);
};
