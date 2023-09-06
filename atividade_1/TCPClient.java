package atividade_1;

/**
 * TCPClient: Cliente para conexao TCP
 * Descricao: Abre uma conexão com o servidor e começa um chat
 * Ao enviar "PARAR", a conexão é finalizada e ele sai.
 */

import java.net.*;
import java.io.*;
import java.util.Scanner;

public class TCPClient {
	public static void main (String args[]) {
	    Socket clientSocket = null; // socket do cliente
        Scanner reader = new Scanner(System.in); // ler mensagens via teclado
            
            try{
                /* Endereço e porta do servidor */
                int serverPort = 6666;   
                InetAddress serverAddr = InetAddress.getByName("127.0.0.1");
                
                /* conecta com o servidor */  
                clientSocket = new Socket(serverAddr, serverPort);  
                
                /* cria objetos de leitura e escrita */
                ListenThread listen = new ListenThread(clientSocket);
                DataOutputStream out =new DataOutputStream( clientSocket.getOutputStream());
                listen.start();
                /* protocolo de comunicação */
                String buffer = "";
                while (true) {
                    System.out.print("Mensagem: ");
                    buffer = reader.nextLine(); // lê mensagem via teclado
                
                    out.writeUTF(buffer);      	// envia a mensagem para o servidor
		
                    if (buffer.equals("PARAR")) break;
                    
                    //System.out.println("Server disse: " + buffer);
                } 
	    } catch (UnknownHostException ue){
		System.out.println("Socket:" + ue.getMessage());
            } catch (EOFException eofe){
		System.out.println("EOF:" + eofe.getMessage());
            } catch (IOException ioe){
		System.out.println("IO:" + ioe.getMessage());
            } finally {
                try {
                    clientSocket.close();
                } catch (IOException ioe) {
                    System.out.println("IO: " + ioe);;
                }
            }
     } //main
} //class

class ListenThread extends Thread {
    DataInputStream in;
    Socket clientSocket;

    public ListenThread(Socket clientSocket) {
        try {
            this.clientSocket = clientSocket;
            in = new DataInputStream(clientSocket.getInputStream());
        } catch (IOException ioe) {
            System.out.println("Connection:" + ioe.getMessage());
        } //catch
    } //construtor

    /* metodo executado ao iniciar a thread - start() */
    @Override
    public void run() {
        try {
            String buffer = "";
            while (true) {
                buffer = in.readUTF();   /* aguarda o envio de dados */

                System.out.println("\nServer disse: " + buffer);
                System.out.print("Mensagem: ");
                if (buffer.equals("PARAR")) break;
            }
        } catch (EOFException eofe) {
            System.out.println("EOF: " + eofe.getMessage());
        } catch (IOException ioe) {
            System.out.println("IOE: " + ioe.getMessage());
        } finally {
            try {
                in.close();
                clientSocket.close();
            } catch (IOException ioe) {
                System.err.println("IOE: " + ioe);
            }
        }
        System.out.println("Thread comunicação servidor finalizada.");
    } //run
}
