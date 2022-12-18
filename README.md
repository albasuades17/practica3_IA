Hem fet que en l'execució del segon exercici es puguin anar guardant les taules utilitzades
cada cert temps, per així no perdre el procés.
Per fer-ho s'utilitza els mètodes saveTable, per guardar les taules en diversos fitxers de text (un per cada taula), 
i loadTable, per després recuperar-les i guardar-les en els diccionaris que s'utilitzen en l'execució.

En el mètode QlearningWhitesVsBlacksEpsilon surt en un comentari com fer un load de la taula, 
i pel que va al save, ja es va fent durant l'execució per defecte. 
Per canviar el nom del fitxer, s'ha de fer a partir dels mètodes saveTable i loadTable.