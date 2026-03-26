;+++++++++++++++++++++++++++++++++++++++++++++++
%L TOOL_CHECK_POS
;+++++++++++++++++++++++++++++++++++++++++++++++
#MSG["Inspección de herramienta: Posición inicial"]
G01 ZP105 FP104         ; Posición de verificación
G201 #AXIS [Z]          ; Intervención manual
M0
G202
#SYNC POS
P211=V.A.TPOS.Z         ; Posición de inicio de verificación

#RET

;+++++++++++++++++++++++++++++++++++++++++++++++
%L TOOL_CHECK_INC
;+++++++++++++++++++++++++++++++++++++++++++++++
#MSG["Inspección de herramienta: Mov. incremental"]

P212=P211+P126

$DO
    G01 ZP212 FP104     ; Posición carro para verificación
    M0
    P212=P212+P126
    $IF[P212>=P101]     ; Tramo final
        G01 ZP101 FP104 ; Posición final carro para verificación
        M0
    $ENDIF
$ENDDO[P212<P101]

G01 ZP100 FP104         ; Posición inicial carro (104)
#MSG[""]
#FLUSH
#WARNING["ATENCION: Retirar camara"]
M0
#FLUSH
#WARNING[""]

#RET

;+++++++++++++++++++++++++++++++++++++++++++++++
%Broaching_Cycle
;+++++++++++++++++++++++++++++++++++++++++++++++

;-----------------------------------------------
; Comprobación de datos programados
;-----------------------------------------------

$IF[[V.MTB.P[24]<= 0]+[V.MTB.P[24]>5000]] ; Avance carro verificación ranura anillo
    P104 = 5000
$ELSE
    P104 = V.MTB.P[24]
$ENDIF

$IF[[V.MTB.P[25]<= 0]+[V.MTB.P[25]> V.MTB.P[1]]] ; Posición Z para verificar ranura
    P105 = 500
$ELSE
    P105 = V.MTB.P[25]
$ENDIF

$IF[[V.MTB.P[26]<= 0]+[V.MTB.P[26]>2000]] ; Avance plato en verificación ranura anillo
    P116 = 2000
$ELSE
    P116 = V.MTB.P[26]
$ENDIF

$IF[[P121==1]*[P102>V.MTB.P[27]]]
    #ERROR["Avance de acabado programado no permitido F=%D",P102]
$ENDIF


$IF[P120 == 0]                  ; Probeta plana
    P110 = 90                   ; Posición inicial del plato
    P112 = 1                    ; Número de ranuras
    P113 = 0                    ; Paso entre ranuras
$ENDIF

$IF[P112 == 0]                  ;Ranuras
    #ERROR["No se ha programado número de ranuras"]
$ENDIF

$IF[P100 >= P101]               ;Posición carro
     #ERROR["Posición inicial o final mal programados"]
$ENDIF

$IF [FRACT[P113]!=0]
    #ERROR["El paso entre ranuras debe ser número entero"]
$ENDIF

$IF [[FRACT[P112]!=0]+[P112>360]]
    #ERROR["El número ranuras debe ser entero y < 360"]
$ENDIF

$IF[P113 == 0]                  ;Ranuras
    P202=360/P112

    $IF [FRACT[P202]!=0]
        #ERROR["El 360 entre número ranuras debe ser entero"]
    $ENDIF

$ELSEIF [[P112*P113]>360]
     #ERROR[" Número de ranuras por paso no debe superar 360º"]
$ELSE
    P202=P113
$ENDIF

$IF[P100>=V.[1].MPA.NEGLIMIT.Z+10] ; Vigilancia de Z inicial
    #WARNING["ATENCION: Se ha modificado posición inicial del eje Z=%D",P100]
    M0
    #FLUSH
    #WARNING[""]
$ENDIF

$IF[P101<=V.[1].MPA.POSLIMIT.Z-15] ; Vigilancia de Z final
    #WARNING["ATENCION: Se ha modificado el recorrido del eje Z=%D",P101]
    M0
    #FLUSH
    #WARNING[""]
$ENDIF

$IF[[P126<=0]*[[P120==2]+[P126==1]]]
    #ERROR["Incremento en Inspección de herramienta mal programado"]
$ENDIF

$IF[[P125>P112]*[[P120==2]+[P126==1]]]
    #WARNING["Numero de ranuras para Inspección mayor que ranuras programadas"]
    M0
    #FLUSH
    #WARNING[""]
$ENDIF

;Avance eje Z en posicionamientos
$IF[V.MTB.P[22]<=0]
    P103 = V.[1].MPA.G00FEED[1].Z
$ELSE
    P103 = V.MTB.P[22]
$ENDIF

;Avance eje C en posicionamientos
$IF[V.MTB.P[23]<=0]
    P114 = V.[1].MPA.G00FEED[1].C
$ELSE
    P114 = V.MTB.P[23]
$ENDIF




;Lineas añadidas por el CFAA para evitar errores de posicionamiento de plato en ranuras
;$IF [FRACT[P110/4]!=0]
;    #ERROR["El ángulo de la ranura inicial actual programada no es divisible de forma entera de 4º. Si quiere modificar conscientemente este parametro debe modificar la linea 139 del programa -Broaching Cycle-]
;$ENDIF

;$IF [P110-P220!=3]
;     #ERROR["El ángulo de la ranura inicial actual programada no esta a 3º de la ranura anterior realizada.Si quiere modificar conscientemente este parametro debe modificar la linea 154 del programa "Broaching Cycle""]
;$ENDIF

$IF [P110-P220!=P113]
     #ERROR["El ángulo de la ranura inicial actual programada es INCORRECTO verificar el valor de la ultima ranura el valor P220.Si quiere modificar conscientemente este parametro debe modificar la linea 154 del programa "Broaching Cycle""]
$ENDIF


;-----------------------------------------------
; Condiciones iniciales
;-----------------------------------------------

M10                             ; Plato bloqueado
G53
D0
P200=0 P201=0 P205=P125 P206=0
#SYNC POS

$IF[V.[1].G.FRO !=100]
    #WARNING["Comprobar el Feed Override"]
    M0
    #FLUSH
    #WARNING[""]
$ENDIF

;-----------------------------------------------
; Operaciones de mecanizado
;-----------------------------------------------

M20 M9                          ; Retroceso cepillo, paro taladrina
G01 G07 G90 G94 ZP100 FP103     ; Posición inicial carro
G01 CP200 FP114                 ; Posición inicial plato

$IF[P120==1]                    ; Probeta tipo anillo

    $IF[P121==0]                ; Desbaste
        #MSG["VERIFICAR POSICIÓN DE RANURA"]
        G01 ZP105 FP104         ; Posición de verificación
        P206=1
        M0

        $IF [P115==0]
            M8                  ; Taladrina
        $ENDIF
        M100                    ; Inicio de brochado
        G04 K3
        #DSTOP                  ; Deshabilitar la señal de stop.
        #DFHOLD                 ; Deshabilitar la señal de feed-hold.
        G01 ZP101 FP102         ; Posición final carro
        #ESTOP                  ; Habilitar la señal de stop.
        #EFHOLD                 ; Habilitar la señal de feed-hold.
        M21                     ; Avance cepillo
        G01 ZP100 FP103         ; Posición inicial carro (102)
        M101 M20                ; Final de brochado
        #MSG[""]
    $ELSE                       ; Acabado
        #MSG["VERIFICAR CANAL-PASO RANURA-Nr RANURA"]
        G01 ZP100 FP104         ; Posición inicial carro
        G01 CP110 FP116         ; Posición 1a ranura
        G01 ZP105 FP104         ; Posición de verificación
        M0
        G01 ZP100 FP104         ; Posición inicial carro
        G01 C[P110+P202] FP116  ; Posición 2a ranura
        G01 ZP105 FP104         ; Posición de verificación
        M0
        G01 ZP100 FP104         ; Posición inicial carro
        G01 C[P110+[[P112-1]*P202]] FP116  ; Posición N ranura
        G01 ZP105 FP104         ; Posición de verificación
        M0
        G01 ZP100 FP104         ; Posición inicial carro
        G01 CP110 FP116         ; Posición inicial plato
        #MSG[""]
    $ENDIF

$ELSEIF[P120==2]                ; Inspección de herramienta
        LL TOOL_CHECK_POS       ; Posicion
        LL TOOL_CHECK_INC       ; Incremento
$ENDIF

$IF[P120<2]                     ; Probeta Plana/Anillo

    P200=P110
    $IF [P115==0]
        M8                      ; Taladrina
    $ENDIF

    $DO
        G01 CP200 FP114
        $IF[P206==1]            ; Parada inicio capturas
            M0
            P206=0
        $ENDIF

    $IF [P115==0]               ; Modificado 24/05/2021
        M8                      ; Taladrina
    $ENDIF
        $IF[V.[1].G.FRO !=100]
            #WARNING["Comprobar el Feed Override"]
            M0
            #FLUSH
            #WARNING[""]
        $ENDIF
        M100                    ; Inicio de brochado
        #DSTOP                  ; Deshabilitar la señal de stop.
        #DFHOLD                 ; Deshabilitar la señal de feed-hold.
	;M0			;

        G04 KP221                ;ESPERA INGETEAM

	;MECANIZADO ORIGINAL

	;##################################### FAGORTUNE #######################################
	#PATH  ["C:\FAGORCNC\USERS\PRG\FAGOR_TUNE\CMD_EXE_PRG\SUB"]
	V.P.FAGORDATAREPORT = 1
	#PCALL FAGORTUNE_CMD_EXE_INIT.NC  

	V.P.AXIS1=1 ;axis logic number Z
	V.P.AXIS2=2 ;axis logic number C
	V.P.AXIS3=3 ;axis logic number Z1

	V.P.CMD_NAXIS=3
	V.P.CMD_TUNE_AXIS=0;All axis

	;#PCALL FAGORTUNE_SERCOS.NC
	#FLUSH
	
	;-----------Z--------------
	#DEF "TUNE_AXIS"="Z"
	V.P.CMD_TUNE_AXIS=1 ;axis logic number

	V.P.OSCILO_CAPTURE_TRIGGER=1       ;Trigger --> 0 = Deactivated // 1 = Activated
	V.P.OSCILO_CAPTURE_CHANNEL=1        ;Trigger channel
	V.P.OSCILO_CAPTURE_FLANK=1          ;Flank --> 0 = Down  // 1 = Up
	V.P.OSCILO_CAPTURE_LEVEL=6000000          ;Trigger level
	V.P.OSCILO_CAPTURE_POSITION=5      ;Position %
	V.P.OSCILO_CAPTURE_NSAMPLE=8192     ;nSamples
	V.P.OSCILO_CAPTURE_TSAMPLE=1        ;tSample --> ms
	V.P.OSCILO_CAPTURE_NUMBER=P201+1       ;1, 2, 3, 4... For diferent names
	
	;-----------CAPTURA--------------
	;#PCALL FAGORTUNE_OSCILO_CAPTURE.NC
	
	;#######################################################################################

	G01 G07 ZP101 FP102	; Mecanizado REFERENCIA

	;TURBINE 1 BROCHA 0°

	;G01 G05 Z2000 F18000	; Mecanizado Brocha 01
	;G01 G07 ZP101 F5000	; Mecanizado Brocha Apertura lateral

	;TURBINE 1 BROCHA 15°

	;G01 G05 Z2400 F18000	; Mecanizado Brocha 01
	;G01 G07 ZP101 F5000	; Mecanizado Brocha Apertura lateral

	;TURBINE 2 BROCHAS 0°

	;G01 G05 Z1370 F18000	; Mecanizado Brocha 01
	;G01 Z1877 F5000	; Mecanizado Brocha Apertura lateral
	;G01 Z2686 F18000	; Mecanizado Brocha 02
	;G01 G07 ZP101 F5000	; Mecanizado Brocha Apertura lateral

	;TURBINE 2 BROCHAS 15°

	;G01 G05 Z1334 F18000	; Mecanizado Brocha 01
	;G01 Z1776 F5000	; Mecanizado Brocha Apertura lateral
	;G01 Z2638 F18000	; Mecanizado Brocha 02
	;G01 G07 ZP101 F5000	; Mecanizado Brocha Apertura lateral

	;MECANIZADO PARAMETRIZADO

	;G01 G05 ZP106 FP102	; Mecanizado (P102=Vc programada / P106=Variable general[Z intermedio])
        ;G01 G07 ZP101 FP102     ; Mecanizado (P101=Final de carrera / P108=Variable general[Vc final])

	P250=P250+1		; Aumenta 1ud el nombre del ensayo 
        #ESTOP                  ; Habilitar la señal de stop.
        #EFHOLD                 ; Habilitar la señal de feed-hold.

        G01 CP111 FP114         ; Plato a posición de retorno
        M21           ; Avance cepillo
        P220=P200; Modificación CFAA para aumentar seguridad de ensayos. Ver linea 139.

        G01 ZP100 FP103         ; Retorno carro
        M101 M20                ; Final de brochado

        P200=P200+P202
        P201=P201+1

        $IF[[P120==1]*[P122==1]*[P201==P205]] ; Probeta tipo anillo con Inspección
            M9                      ; Parada taladrina
            LL TOOL_CHECK_POS       ; Posicion
            LL TOOL_CHECK_INC       ; Incremento
            P205=P205+P125
            $IF [P115==0]
                M8                  ; Taladrina
            $ENDIF
        $ENDIF

    $ENDDO [P201 < P112]

$ENDIF

;-----------------------------------------------
; Fin de operaciones
;-----------------------------------------------

    M9                          ; Desactivar taladrina

#RET

 #COMMENT BEGIN
 P100 = Zi posición de inicio carro
 P101 = Zf posición final del carro
 P102 = F avance carro en mecanizado
 P103 = F avance carro en posicinamiento
 P104 = F avance carro verificación ranura anillo
 P105 = Posición Z para verificar ranura en probeta tipo anillo
 P110 = Posición inicial del plato (No cambia en todo el programa de brochado)
 P111 = Posición plato para retorno carro a origen
 P112 = Número de ranuras
 P113 = Paso entre ranuras
 P114 = F avance plato en posicinamiento
 P115 = Taladrina
 P116 = F avance plato en verificación
 P120 = Tipo de probeta
 P121 = Tipo de mecanizado, Desbaste - Acabado
 P122 = Operación de Inspección de herramienta
 P125 = Numero de ranura ha realizar inspección
 P126 = Incremento eje Z durante inspección
 P200 = Posición angular plato brochado actual
 P201 = ?
 P202 = Paso angular entre brochados
 P205 = ?
 P206 = ?
 P210 = Cota C de posicionamiento desde OP-MAN
 P211 = Cota Z inicio Inspección de herramienta
 P212 = Cota Z en Inspección de herramienta (incremental)
 
 Añadidas por CFAA
 P220 = Posición angular del plato del último brochado (No cambiar nunca el valor salvo que se sepa que se está haciendo) 
 P250 = Nombre del ensayo asociado a cada ranura


 M10 = Plato como eje muerto. Se bloquea despues del movimiento
 M8 = Taladrina
 M20 = Retroceso cepillo de limpieza
 M21 = Avance cepillo de limpieza
 V.MTB.P[20] = Zi posición de inicio carro
 V.MTB.P[21] = Zf posición final del carro
 V.MTB.P[22] = Avance eje Z en posicionamientos
 V.MTB.P[23] = Avance eje C en posicionamientos
 V.MTB.P[24] = Avance carro verificación ranura anillo
 V.MTB.P[25] = Posición Z para verificar ranura
 V.MTB.P[26] = Avance plato en verificación ranura anillo
 V.MTB.P[27] = Máx. Avance eje Z mecanizado acabado
 #COMMENT END