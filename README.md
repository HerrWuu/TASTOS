1. 关于多线程数据流向
    主线程 -> input_queue -> PCB检测 -> seg_queue -> 分割模型 -> pcb_queue -> PIN检测 -> result_queue -> 主线程

2. main只负责界面和图像传递

3. 注意模型load， 只在第一次启动会load
