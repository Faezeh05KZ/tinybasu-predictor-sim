    li   rx1, 1
    lui  rx0, 0
    addi rx2, rx0, 2
    addi rx3, rx0, 31
    addi rx3, rx3, 20
outer:
    addi rx4, rx0, 0
    addi rx6, rx2, 0
    addi rx5, rx0, 0
inner:
    add  rx4, rx4, rx1
    addi rx5, rx5, 1
    bne  rx5, rx6, inner
    addi rx1, rx4, 0
    addi rx2, rx2, 1
    bne  rx2, rx3, outer
