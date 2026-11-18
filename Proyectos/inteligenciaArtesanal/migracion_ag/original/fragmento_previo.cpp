// PDF 1, libro 294. Final de un programa del apéndice anterior.
// El comienzo, tipos, función y permutaciones no están en a.pdf.
auxiliar.genes[permuta[mejorCromosoma][0]] = individuo.genes[v[0]];
auxiliar.genes[permuta[mejorCromosoma][1]] = individuo.genes[v[1]];
auxiliar.genes[permuta[mejorCromosoma][2]] = individuo.genes[v[2]];
for (int i = 0;i < individuo.lonCrom;i++){
    individuo.genes[i] = auxiliar.genes[i];
    }
  }
}
