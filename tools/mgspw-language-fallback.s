// Peace Walker 1.3.0 main BCA1A793E41A4836EF3C03286B18E816EEC62338
// Assemble at flat 0x5F7D0; IPS32 offset 0x5F8D0 includes the NSO header.
// Preserve explicit launcher languages; query ProgramId only for the fallback.
// GetInfo SVC 0x29 is allowed by this release main.npdm.
adrp x8, 0x27316000
 ldr x8, [x8, #0xd70]
 ldr x8, [x8, #0x70]
 cbz x8, fallback
 ldrb w9, [x8]
 cbz w9, fallback
 ldrb w10, [x8,#1]
 orr w9,w9,w10,lsl #8
mov w10, #28261
 cmp w9,w10
 b.eq lang0
mov w10, #29286
 cmp w9,w10
 b.eq lang1
mov w10, #28787
 cmp w9,w10
 b.eq lang4
mov w10, #29287
 cmp w9,w10
 b.eq lang2
mov w10, #29801
 cmp w9,w10
 b.eq lang3
mov w10, #28778
 cmp w9,w10
 b.eq lang6
mov w10, #29808
 cmp w9,w10
 b.eq lang4
fallback: mov x1,#18
 mov x2,#0x8001
 movk x2,#0xffff,lsl #16
 mov x3,#0
 svc #0x29
 cbnz w0,lang6
 mov x8,#0xa000
 movk x8,#0x1c4f,lsl #16
 movk x8,#0x9980,lsl #32
 movk x8,#0x0100,lsl #48
 cmp x1,x8
 b.eq lang0
 b lang6
lang0: mov w0,#0
 ret
lang1: mov w0,#1
 ret
lang2: mov w0,#2
 ret
lang3: mov w0,#3
 ret
lang4: mov w0,#4
 ret
lang6: mov w0,#6
 ret
