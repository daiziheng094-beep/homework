COMMENT xstate: READS flat file of cross-state teen data;

data check;
title1 '1989-92 cross-state comparisons -- chapter 4 models';

infile '/home/decard/minbook/fedmin/teens/tn8992.dat';

input state $ 1-9 fips temp86-temp92 emp86-emp92 ur86-ur92
      submin89 atmin89 affect1 affect2 submin92 atmin92
      lwage89 lwage92 std89 std92 lwmen89 lwmen92 n_89; 

label fips='fips state code'
      temp86='teenage epop rate, 1986'
      emp86='overall epop rate 1986'
      ur86='unempl. rate 1986'
      temp92='teenage epop rate, 1992'
      emp92='overall epop rate 1992'
      ur92='unempl. rate 1992'
      submin89='frac wage <$3.35/hr, 1989' 
      submin92='frac wage <$4.25/hr, 1992'
      atmin89='fract wage = $3.35, 1989'
      atmin92='fract wage = $4.25, 1992'
      affect1='fract wage $3.35-3.799, 1989'
      affect2='fract wage $3.35-4.249, 1989'
      lwage89='mean log wage teens 1989'
      lwage92='mean log wage teens 1992'
      std89='std dev of log teen wage, 1989'
      std92='std dev of log teen wage, 1992'
      lwmen89='mean log wage men age25+, 1989'
      lwmen92='mean log wage men age25+, 1992'
      n_89='# teens in cps extract, 1989';

 

DTEMP1=TEMP91-TEMP89;                                                           
DTEMP2=TEMP92-TEMP89;                                                           
DEMP1=EMP91-EMP89;                                                              
DEMP2=EMP92-EMP89;                                                              
DWAGE2=LWAGE92-LWAGE89;                                                         
dwmen=lwmen92-lwmen89;                                                                               
dur2=ur92-ur89;

proc means;
title2 'check on output of basic teen data';
var temp86-temp92 emp86-emp92 ur86-ur92
    submin89 atmin89 affect1 affect2 submin92 atmin92
    lwage89 lwage92 std89 std92 lwmen89 lwmen92 n_89;                          
                                                                                

proc corr;
var dtemp2 dwage2 demp2 dur2 dwmen;

PROC PRINT;                                                                     
VAR STATE FIPS TEMP89-TEMP92 EMP89-EMP92 AFFECT1 AFFECT2;                


*basic models from myth and measurement, table 4.4, panel c;

proc reg;
model dwage2=affect2;
model dwage2=affect2 demp2;
model dwage2=affect2 demp2 dwmen;
model dtemp2=affect2;
model dtemp2=affect2 demp2;
model dtemp2=affect2 demp2 dwmen;
WEIGHT N_89;                                                                    













                                                                               

