export const bounds = [118.72, 31.990, 118.878, 32.112];
export function tileXY(lon, lat) {
  const t = Math.PI * lat / 180;
  return [(lon+180)/360*8192, (1-Math.asinh(Math.tan(t))/Math.PI)*4096];
}
const [west,south,east,north] = bounds;
const [left,top] = tileXY(west,north);
const [right,bottom] = tileXY(east,south);
export function uv(lon,lat) {
  const [x,y] = tileXY(lon,lat);
  return [(x-left)/(right-left),(y-top)/(bottom-top)];
}
export const width = 11.6;
export const height = width*(bottom-top)/(right-left);
