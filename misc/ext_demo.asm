    lui  rx0, 0

    li   rx1, 12
    li   rx2, 10

    and  rx3, rx1, rx2
    mul  rx4, rx1, rx2
    div  rx5, rx1, rx2
    addi rx1, rx0, 2
    sll  rx6, rx2, rx1
    srl  rx7, rx4, rx1

    ori  rx1, rx2, 5
    andi rx2, rx1, 9
    slti rx3, rx2, 20

    li   rx4, 5
    li   rx5, 8
    bgt  rx5, rx4, is_greater
    li   rx6, 0
    jmp  after_bgt
is_greater:
    li   rx6, 9
after_bgt:

    li   rx4, 3
    li   rx5, 9
    blt  rx4, rx5, is_less
    li   rx7, 0
    jmp  after_blt
is_less:
    li   rx7, 19
after_blt:

    li   rx1, jr_target
    jr   rx1
    li   rx2, 29
jr_target:
    li   rx2, 31
