"""实际 PNG 的局部客观判据；不评审审美，不维护跨机器黄金图。"""
import json
from pathlib import Path
import struct
import zlib
from routes import validate_sample


def png(path: Path):
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("非 PNG")
    offset = 8; payload = b""; width = height = channels = None
    while offset < len(raw):
        size = struct.unpack_from(">I", raw, offset)[0]
        kind = raw[offset+4:offset+8]; data = raw[offset+8:offset+8+size]
        if zlib.crc32(kind+data) & 0xffffffff != struct.unpack_from(">I", raw, offset+8+size)[0]:
            raise ValueError("PNG CRC 错误")
        if kind == b"IHDR":
            width,height,depth,color,compression,filter_,interlace = struct.unpack(">IIBBBBB",data)
            if depth != 8 or color not in [2,6] or interlace != 0:
                raise ValueError("只支持 RGB/RGBA 8 位非交错")
            channels=3 if color==2 else 4
        if kind == b"IDAT": payload += data
        offset += size+12
        if kind == b"IEND": break
    decoded=zlib.decompress(payload); stride=width*channels; rows=[]; previous=bytearray(stride); cursor=0
    for _ in range(height):
        filter_=decoded[cursor]; cursor+=1; row=bytearray(decoded[cursor:cursor+stride]);cursor+=stride
        for i in range(stride):
            a=row[i-channels] if i>=channels else 0; b=previous[i]; c=previous[i-channels] if i>=channels else 0
            if filter_==1: prediction=a
            elif filter_==2: prediction=b
            elif filter_==3: prediction=(a+b)//2
            elif filter_==4:
                p=a+b-c; distances=[abs(p-a),abs(p-b),abs(p-c)]; prediction=[a,b,c][distances.index(min(distances))]
            elif filter_==0: prediction=0
            else: raise ValueError("无效 PNG filter")
            row[i]=(row[i]+prediction)%256
        rows.append(row);previous=row
    return width,height,channels,rows


def ratio(image, point, predicate):
    width,height,channels,rows=image; x,y=map(round,point)
    if not 12<=x<width-12 or not 12<=y<height-12:
        raise ValueError("对象投影超出画面")
    values=[rows[j][i*channels:i*channels+3] for j in range(y-10,y+11) for i in range(x-10,x+11)]
    return sum(predicate(*v) for v in values)/len(values)


def verify_frames(directory: Path, route: str) -> dict:
    frames=[png(directory/f"frame-{n}.png") for n in [1,2,3]]
    states=[json.loads((directory/f"frame-{n}.json").read_text(encoding="utf8")) for n in [1,2,3]]
    for state in states:
        validate_sample(state, route)
    blue=lambda r,g,b: b>r*1.4 and g>r*1.3 and b>60
    gold=lambda r,g,b: r>b*1.5 and g>b*1.3 and r>60
    results={"player_visible_start":ratio(frames[0],states[0]["actor_pixel"],blue),
             "target_visible_start":ratio(frames[0],states[0]["target_pixel"],gold),
             "target_hidden_after":ratio(frames[1],states[1]["target_pixel"],gold),
             "player_visible_after":ratio(frames[1],states[1]["actor_pixel"],blue)}
    if results["player_visible_start"]<0.5 or results["target_visible_start"]<0.5 or results["target_hidden_after"]>0.02 or results["player_visible_after"]<0.5:
        raise RuntimeError(f"局部像素断言失败: {results}")
    if not states[1]["state"]["activated"] or not states[2]["state"]["paused"]:
        raise RuntimeError("截图同帧状态不符")
    # 反例使用同一局部区域判据，不以某个常量判定器单独返回 false 冒充。
    def recolor(image, point, color):
        width,height,channels,rows=image
        copy=[bytearray(row) for row in rows]
        x,y=map(round,point)
        for j in range(y-10,y+11):
            for i in range(x-10,x+11):
                copy[j][i*channels:i*channels+3]=bytes(color)
        return width,height,channels,copy
    for color in [(50,60,70), (220,180,20)]:
        if ratio(recolor(frames[0],states[0]["actor_pixel"],color), states[0]["actor_pixel"],blue)>=0.5:
            raise RuntimeError("隐藏／错色反例失效")
    if ratio(frames[0],states[0]["target_pixel"],blue)>=0.5:
        raise RuntimeError("错位反例失效")
    return results
