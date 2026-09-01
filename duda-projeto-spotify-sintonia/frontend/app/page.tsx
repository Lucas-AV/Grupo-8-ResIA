import { CartaoAgente } from '@/componentes/CartaoAgente';
import { CartaoFaixa } from '@/componentes/CartaoFaixa';
import { MapaMusical } from '@/componentes/MapaMusical';

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

const agentes = [
  ['01', 'Orquestrador', 'Identifica a intenção e coordena os módulos necessários.'],
  ['02', 'Coleta Spotify', 'Obtém somente os dados autorizados e registra sua origem.'],
  ['03', 'ETL', 'Limpa, valida e prepara dataset e sinais do usuário.'],
  ['04', 'Clustering', 'Classifica faixas e usuário em perfis interpretáveis.'],
  ['05', 'Conversacional', 'Transforma resultados estruturados em diálogo natural.'],
  ['06', 'Confiança e HITL', 'Bloqueia respostas abaixo de 90% e solicita revisão.'],
];

export default function PaginaInicial() {
  return (
    <main>
      <header className="topo">
        <a className="marca" href="#inicio" aria-label="Spotify Insights, início">
          <span className="marca-icone"><i /><i /><i /></span>
          <span>Spotify Insights<span className="ponto">.</span></span>
        </a>
        <nav aria-label="Navegação principal">
          <a href="#conversa">Conversa</a>
          <a href="#descobertas">Descobertas</a>
          <a href="#agentes">Agentes</a>
        </nav>
        <span className="selo">Projeto UnB</span>
      </header>

      <section className="apresentacao" id="inicio">
        <div>
          <span className="rotulo">Recomendação explicável</span>
          <h1>Descobrir música sem depender de uma caixa-preta.</h1>
          <p>Clustering interpretável, controle do usuário e revisão humana quando a confiança for menor que 90%.</p>
          <div className="acoes">
            <a className="botao-spotify" href={`${apiUrl}/auth/spotify/iniciar`}>Conectar Spotify</a>
            <a href="#agentes">Conhecer a arquitetura</a>
          </div>
        </div>
        <div className="regra-confianca">
          <span>Regra crítica</span>
          <strong>90%</strong>
          <p>Abaixo do limiar, nenhuma resposta automática.</p>
        </div>
      </section>

      <section className="grade-principal" id="conversa">
        <div className="chat">
          <div className="cabecalho-chat">
            <span className="pulso" />
            <div><span className="rotulo">Orquestrador</span><h2>Conversa em construção</h2></div>
          </div>
          <div className="mensagens">
            <div className="balao agente">
              <p>A estrutura dos agentes está pronta, mas ainda não vou fingir que consigo recomendar.</p>
              <p>O próximo passo é validar o dataset e treinar o clustering no notebook.</p>
            </div>
            <div className="balao usuario"><p>Quero uma descoberta diferente.</p></div>
            <div className="balao revisao"><p>TODO: esta mensagem será processada pelo Orquestrador e pelo gate de confiança.</p></div>
          </div>
          <form className="entrada-chat">
            <label className="somente-leitor" htmlFor="mensagem">Converse com o chatbot</label>
            <input id="mensagem" disabled placeholder="Chat disponível após a implementação do backend" />
            <button type="button" disabled aria-label="Enviar">↗</button>
          </form>
        </div>
        <MapaMusical />
      </section>

      <section className="descobertas" id="descobertas">
        <div className="titulo-secao">
          <div><span className="rotulo">Contrato visual preservado</span><h2>Recomendação com justificativa e confiança</h2></div>
          <span className="aviso">Dados ilustrativos — não são recomendação</span>
        </div>
        <CartaoFaixa
          nome="Faixa de exemplo"
          artista="Artista de exemplo"
          explicacao="O card já reserva espaço para sinais do cluster, novidade e justificativa verificável."
          confianca={0.94}
        />
      </section>

      <section className="secao-agentes" id="agentes">
        <div className="titulo-secao"><div><span className="rotulo">Arquitetura modular</span><h2>Seis responsabilidades, um único fluxo auditável</h2></div></div>
        <div className="grade-agentes">
          {agentes.map(([numero, nome, descricao]) => <CartaoAgente key={numero} numero={numero} nome={nome} descricao={descricao} />)}
        </div>
      </section>

      <footer>
        <span>Spotify Insights & Recommender Chatbot · UnB</span>
        <span>Estrutura inicial — sem recomendações reais nesta fase.</span>
      </footer>
    </main>
  );
}
