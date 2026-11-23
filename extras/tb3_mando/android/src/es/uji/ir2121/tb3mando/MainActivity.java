package es.uji.ir2121.tb3mando;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Bundle;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InterfaceAddress;
import java.net.NetworkInterface;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class MainActivity extends Activity {
    private WebView web;
    private volatile boolean downloading = false;
    private volatile boolean cancelDownload = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new Bridge(), "Android");
        setContentView(web);
        web.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onPause() {
        super.onPause();
        web.evaluateJavascript("typeof release==='function'&&release()", null);
    }

    private void js(final String code) {
        runOnUiThread(new Runnable() {
            public void run() {
                web.evaluateJavascript(code, null);
            }
        });
    }

    private static List<String[]> candidateNetworks() {
        List<String[]> nets = new ArrayList<String[]>();
        try {
            for (NetworkInterface ni : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!ni.isUp() || ni.isLoopback()) continue;
                String name = ni.getName();
                for (InterfaceAddress ia : ni.getInterfaceAddresses()) {
                    InetAddress a = ia.getAddress();
                    if (!(a instanceof Inet4Address)) continue;
                    String ip = a.getHostAddress();
                    if (ip.startsWith("127.")) continue;
                    boolean usb = name.startsWith("rndis") || name.startsWith("usb") || name.startsWith("ncm");
                    boolean wifi = name.startsWith("wlan") || name.startsWith("ap") || name.startsWith("swlan");
                    if (usb || wifi) {
                        String[] n = new String[]{name, ip, usb ? "1" : "0"};
                        if (usb) nets.add(0, n); else nets.add(n);
                    }
                }
            }
        } catch (Exception e) {
        }
        return nets;
    }

    private static JSONObject ping(String ip, int port, int timeoutMs) {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL("http://" + ip + ":" + port + "/api/ping").openConnection();
            c.setConnectTimeout(timeoutMs);
            c.setReadTimeout(timeoutMs);
            if (c.getResponseCode() != 200) return null;
            BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line);
            JSONObject o = new JSONObject(sb.toString());
            if (!"tb3_phone".equals(o.optString("app"))) return null;
            JSONObject res = new JSONObject();
            res.put("ip", ip);
            res.put("robot", o.optString("robot", "robot"));
            return res;
        } catch (Exception e) {
            return null;
        } finally {
            if (c != null) c.disconnect();
        }
    }

    private String saveStream(InputStream in, String name, long total) throws Exception {
        OutputStream out;
        Uri uri = null;
        File file = null;
        String where;
        ContentResolver cr = getContentResolver();
        if (Build.VERSION.SDK_INT >= 29) {
            ContentValues v = new ContentValues();
            v.put("_display_name", name);
            v.put("mime_type", "application/zip");
            v.put("relative_path", Environment.DIRECTORY_DOWNLOADS + "/TB3");
            v.put("is_pending", 1);
            uri = cr.insert(Uri.parse("content://media/external/downloads"), v);
            if (uri == null) throw new Exception("Android no deja crear el archivo en Descargas");
            out = cr.openOutputStream(uri);
            where = "Descargas/TB3/" + name;
        } else {
            File dir = new File(getExternalFilesDir(null), "TB3");
            dir.mkdirs();
            file = new File(dir, name);
            out = new FileOutputStream(file);
            where = file.getAbsolutePath();
        }
        boolean ok = false;
        try {
            byte[] buf = new byte[1 << 16];
            long done = 0, last = 0, t0 = System.currentTimeMillis();
            int n;
            while ((n = in.read(buf)) > 0) {
                if (cancelDownload) throw new Exception("cancelada");
                out.write(buf, 0, n);
                done += n;
                long now = System.currentTimeMillis();
                if (now - last > 300) {
                    last = now;
                    double secs = Math.max(0.001, (now - t0) / 1000.0);
                    js("onDownloadProgress(" + done + "," + total + "," + (long) (done / secs) + ")");
                }
            }
            out.flush();
            ok = true;
            js("onDownloadProgress(" + done + "," + total + ",0)");
        } finally {
            try {
                out.close();
            } catch (Exception e) {
            }
            if (uri != null) {
                if (ok) {
                    ContentValues v = new ContentValues();
                    v.put("is_pending", 0);
                    cr.update(uri, v, null, null);
                } else {
                    cr.delete(uri, null, null);
                }
            }
            if (file != null && !ok) file.delete();
        }
        return where;
    }

    public class Bridge {
        @JavascriptInterface
        public boolean canDownload() {
            return true;
        }

        @JavascriptInterface
        public void cancelDownload() {
            cancelDownload = true;
        }

        @JavascriptInterface
        public void download(final String url, final String token) {
            if (downloading) return;
            downloading = true;
            cancelDownload = false;
            new Thread(new Runnable() {
                public void run() {
                    HttpURLConnection c = null;
                    try {
                        c = (HttpURLConnection) new URL(url).openConnection();
                        c.setRequestProperty("X-Token", token);
                        c.setConnectTimeout(5000);
                        c.setReadTimeout(60000);
                        int code = c.getResponseCode();
                        if (code != 200) {
                            String msg = code == 401 ? "PIN incorrecto" : code == 409 ? "Ese bag se está grabando. Para la grabación primero." : "error " + code;
                            js("onDownloadDone(false," + JSONObject.quote(msg) + ")");
                            return;
                        }
                        String name = c.getHeaderField("X-File-Name");
                        if (name == null || name.isEmpty()) name = "tb3_datos.zip";
                        long total = 0;
                        try {
                            total = Long.parseLong(c.getHeaderField("X-Total-Size"));
                        } catch (Exception e) {
                        }
                        String where = saveStream(c.getInputStream(), name, total);
                        js("onDownloadDone(true," + JSONObject.quote(where) + ")");
                    } catch (Exception e) {
                        js("onDownloadDone(false," + JSONObject.quote(String.valueOf(e.getMessage())) + ")");
                    } finally {
                        if (c != null) c.disconnect();
                        downloading = false;
                    }
                }
            }).start();
        }

        @JavascriptInterface
        public void discover(final int port) {
            new Thread(new Runnable() {
                public void run() {
                    final JSONArray found = new JSONArray();
                    List<String[]> nets = candidateNetworks();
                    if (nets.isEmpty()) {
                        js("onDiscoverInfo('No hay red USB ni WiFi activa. Activa «Compartir conexión por USB».')");
                        js("onDiscover([])");
                        return;
                    }
                    StringBuilder where = new StringBuilder();
                    for (String[] n : nets) where.append(n[0]).append(' ').append(n[1]).append("  ");
                    js("onDiscoverInfo(" + JSONObject.quote("Buscando en " + where.toString().trim() + "…") + ")");
                    ExecutorService pool = Executors.newFixedThreadPool(48);
                    for (String[] n : nets) {
                        final String mine = n[1];
                        String prefix = mine.substring(0, mine.lastIndexOf('.') + 1);
                        for (int i = 1; i < 255; i++) {
                            final String ip = prefix + i;
                            if (ip.equals(mine)) continue;
                            pool.execute(new Runnable() {
                                public void run() {
                                    JSONObject o = ping(ip, port, 700);
                                    if (o != null) {
                                        synchronized (found) {
                                            found.put(o);
                                        }
                                    }
                                }
                            });
                        }
                    }
                    pool.shutdown();
                    try {
                        pool.awaitTermination(30, TimeUnit.SECONDS);
                    } catch (InterruptedException e) {
                    }
                    js("onDiscover(" + found.toString() + ")");
                }
            }).start();
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
}
