type Propriedades = {
  numero: string;
  nome: string;
  descricao: string;
  status?: string;
};

export function CartaoAgente({ numero, nome, descricao, status = 'Estrutura pronta' }: Propriedades) {
  return (
    <article className="cartao-agente">
      <span className="numero-agente">{numero}</span>
      <div>
        <span className="status-modulo">{status}</span>
        <h3>{nome}</h3>
        <p>{descricao}</p>
      </div>
    </article>
  );
}

